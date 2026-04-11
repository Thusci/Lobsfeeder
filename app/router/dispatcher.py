from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from time import monotonic
from typing import Any, AsyncIterator

from app.clients.registry import ClientRegistry
from app.core.errors import (
    EvaluatorError,
    HealthCircuitOpenError,
    NoCapacityError,
    RouterError,
    RoutingError,
    UpstreamRateLimitError,
    UpstreamServerError,
    UpstreamTimeoutError,
)
from app.core.settings import AppConfig
from app.evaluator.service import EvaluatorService
from app.ratelimit.estimation import TokenEstimator
from app.ratelimit.manager import ModelLease, RateLimitManager
from app.router.fallback import build_candidates
from app.router.health import HealthTracker
from app.router.policy import should_count_as_health_failure, should_fallback
from app.router.selection import resolve_route_mode
from app.telemetry.metrics import MetricsRegistry


logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    response_json: dict[str, Any]
    selected_model: str
    difficulty: str
    fallback_hops: int
    route_mode: str


@dataclass
class StreamDispatchResult:
    stream: AsyncIterator[bytes]
    selected_model: str
    difficulty: str
    fallback_hops: int
    route_mode: str


class RouterDispatcher:
    def __init__(
        self,
        config: AppConfig,
        clients: ClientRegistry,
        metrics: MetricsRegistry,
        token_estimator: TokenEstimator,
        rate_limits: RateLimitManager,
        health: HealthTracker,
        evaluator: EvaluatorService,
    ) -> None:
        self.config = config
        self.clients = clients
        self.metrics = metrics
        self.token_estimator = token_estimator
        self.rate_limits = rate_limits
        self.health = health
        self.evaluator = evaluator

    def _rate_limit_strategy(self) -> str:
        return self.config.routing.fallback_policy.strategy

    async def _resolve_difficulty(
        self,
        payload: dict[str, Any],
        route_mode: str,
        request_id: str,
    ) -> str:
        routing = self.config.routing
        if route_mode == "bypass" or not routing.enabled:
            return routing.default_difficulty

        try:
            result = await self.evaluator.classify(payload)
            return result.difficulty
        except EvaluatorError as exc:
            self.metrics.inc("evaluator_failures")
            logger.warning(
                "evaluator failed, fallback to default difficulty",
                extra={"request_id": request_id, "error_category": exc.code},
            )
            if routing.strict_mode and not routing.fallback_policy.on_evaluator_error_use_default_difficulty:
                raise RoutingError("Evaluator failed and strict mode is enabled", status_code=502)
            return routing.default_difficulty

    async def _acquire_or_raise(self, model_key: str, estimated_tokens: int) -> ModelLease:
        if not self.health.is_healthy(model_key):
            raise HealthCircuitOpenError(f"Model {model_key} is in cooldown")

        can_accept = await self.rate_limits.can_accept(model_key, estimated_tokens)
        if not can_accept:
            raise NoCapacityError(f"Model {model_key} has no capacity")

        return await self.rate_limits.acquire(model_key, estimated_tokens)

    def _with_usage_fallback(self, response_json: dict[str, Any], estimated_tokens: int, actual_tokens: int) -> dict[str, Any]:
        usage = response_json.get("usage")
        if not isinstance(usage, dict):
            response_json["usage"] = {
                "prompt_tokens": max(estimated_tokens // 2, 1),
                "completion_tokens": max(actual_tokens - max(estimated_tokens // 2, 1), 1),
                "total_tokens": max(actual_tokens, 1),
            }
            return response_json

        total = usage.get("total_tokens")
        if not isinstance(total, int) or total <= 0:
            usage["total_tokens"] = max(actual_tokens, 1)
        return response_json

    @staticmethod
    def _build_upstream_headers(request_id: str) -> dict[str, str]:
        return {"X-Request-ID": request_id}

    async def _queue_for_capacity(self, model_key: str, estimated_tokens: int) -> ModelLease:
        policy = self.config.routing.fallback_policy
        wait_ms = policy.queue_wait_ms
        if wait_ms <= 0:
            raise NoCapacityError(f"Model {model_key} has no capacity and queue_wait_ms=0")

        poll_seconds = policy.queue_poll_interval_ms / 1000.0
        deadline = monotonic() + (wait_ms / 1000.0)
        while monotonic() < deadline:
            if await self.rate_limits.can_accept(model_key, estimated_tokens):
                try:
                    return await self.rate_limits.acquire(model_key, estimated_tokens)
                except NoCapacityError:
                    pass
            await asyncio.sleep(poll_seconds)

        raise NoCapacityError(f"Model {model_key} has no capacity after queue wait")

    async def _acquire_with_strategy(self, model_key: str, estimated_tokens: int) -> ModelLease:
        try:
            return await self._acquire_or_raise(model_key, estimated_tokens)
        except NoCapacityError:
            self.metrics.inc("per_model_rate_limit_hits", {"model": model_key})
            if self._rate_limit_strategy() == "queue":
                return await self._queue_for_capacity(model_key, estimated_tokens)
            raise

    def _should_continue_to_next_candidate(self, exc: Exception, stream_started: bool = False) -> bool:
        if isinstance(exc, (NoCapacityError, UpstreamRateLimitError)):
            return self._rate_limit_strategy() == "fallback"
        return should_fallback(exc, stream_started=stream_started)

    def _record_failure_metrics(self, model_key: str, exc: Exception) -> None:
        self.metrics.inc("failed_requests")
        self.metrics.inc("per_model_fallback_from", {"model": model_key})
        if isinstance(exc, (NoCapacityError, UpstreamRateLimitError)):
            self.metrics.inc("per_model_rate_limit_hits", {"model": model_key})
        if isinstance(exc, UpstreamTimeoutError):
            self.metrics.inc("per_model_timeouts", {"model": model_key})

    async def dispatch_non_stream(self, payload: dict[str, Any], request_id: str) -> DispatchResult:
        started = monotonic()
        self.metrics.inc("total_requests")
        estimated_tokens = self.token_estimator.estimate_request_tokens(payload)

        route_mode = resolve_route_mode(str(payload.get("model", "")), self.config)
        if route_mode.mode == "invalid_override":
            raise RoutingError(
                route_mode.error_message or "Unknown override model",
                status_code=400,
                code="unknown_override",
            )
        difficulty = await self._resolve_difficulty(payload, route_mode.mode, request_id)
        candidates = build_candidates(self.config, difficulty=difficulty, override_model=route_mode.override_model)

        if not candidates:
            raise RoutingError("No available candidates after routing")

        last_error: Exception | None = None
        for hop, model_key in enumerate(candidates):
            lease: ModelLease | None = None
            try:
                lease = await self._acquire_with_strategy(model_key, estimated_tokens)
                client = self.clients.get(model_key)
                response = await client.chat_completions(
                    payload,
                    headers=self._build_upstream_headers(request_id),
                )
                actual_tokens = self.token_estimator.resolve_actual_tokens(response.response_json, estimated_tokens)
                await lease.finalize(actual_tokens)
                self.health.record_success(model_key)

                response_json = self._with_usage_fallback(response.response_json, estimated_tokens, actual_tokens)
                response_json["model"] = model_key

                latency_ms = (monotonic() - started) * 1000
                self.metrics.inc("successful_requests")
                self.metrics.inc("per_model_requests", {"model": model_key})
                self.metrics.observe("per_model_latency_ms", latency_ms, {"model": model_key})

                logger.info(
                    "request served",
                    extra={
                        "request_id": request_id,
                        "difficulty": difficulty,
                        "selected_model": model_key,
                        "fallback_hops": hop,
                    },
                )
                return DispatchResult(
                    response_json=response_json,
                    selected_model=model_key,
                    difficulty=difficulty,
                    fallback_hops=hop,
                    route_mode=route_mode.mode,
                )
            except Exception as exc:
                last_error = exc
                if lease is not None and not lease.finalized:
                    await lease.finalize(estimated_tokens)

                if should_count_as_health_failure(exc):
                    self.health.record_failure(model_key, str(exc))

                self._record_failure_metrics(model_key, exc)

                if hop < len(candidates) - 1 and self._should_continue_to_next_candidate(exc):
                    continue

                if isinstance(exc, RouterError):
                    if self._should_continue_to_next_candidate(exc):
                        raise RoutingError(
                            "All candidate models failed",
                            status_code=503,
                            code="all_backends_unavailable",
                        ) from exc
                    raise
                raise UpstreamServerError(str(exc)) from exc

        if isinstance(last_error, RouterError):
            raise last_error
        raise RoutingError("No candidate model could serve the request")

    async def dispatch_stream(self, payload: dict[str, Any], request_id: str) -> StreamDispatchResult:
        self.metrics.inc("total_requests")
        estimated_tokens = self.token_estimator.estimate_request_tokens(payload)

        route_mode = resolve_route_mode(str(payload.get("model", "")), self.config)
        if route_mode.mode == "invalid_override":
            raise RoutingError(
                route_mode.error_message or "Unknown override model",
                status_code=400,
                code="unknown_override",
            )
        difficulty = await self._resolve_difficulty(payload, route_mode.mode, request_id)
        candidates = build_candidates(self.config, difficulty=difficulty, override_model=route_mode.override_model)
        if not candidates:
            raise RoutingError("No available candidates after routing")

        last_error: Exception | None = None
        for hop, model_key in enumerate(candidates):
            lease: ModelLease | None = None
            stream_cm = None
            stream_entered = False
            try:
                lease = await self._acquire_with_strategy(model_key, estimated_tokens)
                client = self.clients.get(model_key)
                stream_cm = client.stream_chat_completions(
                    payload,
                    headers=self._build_upstream_headers(request_id),
                )
                response = await stream_cm.__aenter__()
                stream_entered = True
                iterator = response.aiter_raw()

                try:
                    first_chunk = await anext(iterator)
                except StopAsyncIteration as exc:
                    raise UpstreamServerError("Upstream stream ended before first chunk") from exc

                self.health.record_success(model_key)
                self.metrics.inc("successful_requests")
                self.metrics.inc("per_model_requests", {"model": model_key})

                async def stream_generator() -> AsyncIterator[bytes]:
                    try:
                        yield first_chunk
                        async for chunk in iterator:
                            yield chunk
                    except Exception as exc:
                        if should_count_as_health_failure(exc):
                            self.health.record_failure(model_key, str(exc))
                        self._record_failure_metrics(model_key, exc)
                        raise
                    finally:
                        await lease.finalize(estimated_tokens)
                        await stream_cm.__aexit__(None, None, None)

                logger.info(
                    "stream request served",
                    extra={
                        "request_id": request_id,
                        "difficulty": difficulty,
                        "selected_model": model_key,
                        "fallback_hops": hop,
                    },
                )
                return StreamDispatchResult(
                    stream=stream_generator(),
                    selected_model=model_key,
                    difficulty=difficulty,
                    fallback_hops=hop,
                    route_mode=route_mode.mode,
                )
            except Exception as exc:
                last_error = exc
                if stream_cm is not None and stream_entered:
                    await stream_cm.__aexit__(type(exc), exc, exc.__traceback__)
                if lease is not None and not lease.finalized:
                    await lease.finalize(estimated_tokens)

                if should_count_as_health_failure(exc):
                    self.health.record_failure(model_key, str(exc))

                self._record_failure_metrics(model_key, exc)

                if hop < len(candidates) - 1 and self._should_continue_to_next_candidate(exc, stream_started=False):
                    continue

                if isinstance(exc, RouterError):
                    if self._should_continue_to_next_candidate(exc, stream_started=False):
                        raise RoutingError(
                            "All candidate models failed",
                            status_code=503,
                            code="all_backends_unavailable",
                        ) from exc
                    raise
                raise UpstreamServerError(str(exc)) from exc

        if isinstance(last_error, RouterError):
            raise last_error
        raise RoutingError("No candidate model could serve stream request")
