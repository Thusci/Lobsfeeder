from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from app.clients.auth import build_upstream_auth_headers
from app.core.errors import (
    ParseError,
    UpstreamAuthError,
    UpstreamClientError,
    UpstreamRateLimitError,
    UpstreamServerError,
    UpstreamTimeoutError,
)
from app.core.settings import ModelConfig


@dataclass
class NormalizedResponse:
    response_json: dict[str, Any]
    actual_tokens: int | None


class OpenAICompatClient:
    def __init__(self, model_key: str, config: ModelConfig) -> None:
        self.model_key = model_key
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_seconds,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _map_error(self, status_code: int, body: str) -> Exception:
        message = body or f"Upstream error status={status_code}"
        if status_code in {401, 403}:
            return UpstreamAuthError(message)
        if status_code == 429:
            return UpstreamRateLimitError(message)
        if status_code >= 500:
            return UpstreamServerError(message)
        return UpstreamClientError(message=message, status_code=status_code, retryable=False)

    async def _post_json(
        self,
        payload: dict[str, Any],
        timeout_seconds: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        merged_headers = dict(build_upstream_auth_headers(self.config))
        if headers:
            merged_headers.update(headers)
        return await self._client.post(
            "/chat/completions",
            json=payload,
            timeout=timeout_seconds or self.config.timeout_seconds,
            headers=merged_headers,
        )

    async def chat_completions(
        self,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> NormalizedResponse:
        req = dict(payload)
        req["model"] = self.config.upstream_model_name

        max_attempts = max(self.config.retry.max_attempts, 1)
        backoff = self.config.retry.backoff_initial_ms / 1000.0
        backoff_max = self.config.retry.backoff_max_ms / 1000.0

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = await self._post_json(req, headers=headers)
                if response.status_code >= 400:
                    body = response.text
                    err = self._map_error(response.status_code, body)
                    if isinstance(err, UpstreamServerError) and attempt < max_attempts:
                        await asyncio.sleep(min(backoff, backoff_max))
                        backoff *= 2
                        continue
                    raise err

                data = response.json()
                if not isinstance(data, dict):
                    raise ParseError("Upstream response was not a JSON object")

                usage = data.get("usage")
                actual_tokens = None
                if isinstance(usage, dict):
                    total = usage.get("total_tokens")
                    if isinstance(total, int):
                        actual_tokens = total

                return NormalizedResponse(response_json=data, actual_tokens=actual_tokens)
            except httpx.TimeoutException as exc:
                last_error = UpstreamTimeoutError(str(exc))
                if attempt < max_attempts:
                    await asyncio.sleep(min(backoff, backoff_max))
                    backoff *= 2
                    continue
                raise last_error
            except ValueError as exc:
                raise ParseError(str(exc)) from exc
            except (UpstreamClientError, UpstreamAuthError, UpstreamRateLimitError, UpstreamServerError):
                raise
            except Exception as exc:  # pragma: no cover
                last_error = UpstreamServerError(str(exc))
                if attempt < max_attempts:
                    await asyncio.sleep(min(backoff, backoff_max))
                    backoff *= 2
                    continue
                raise last_error

        raise UpstreamServerError(str(last_error or "Unknown upstream error"))

    @asynccontextmanager
    async def stream_chat_completions(
        self,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[httpx.Response]:
        req = dict(payload)
        req["model"] = self.config.upstream_model_name

        try:
            merged_headers = dict(build_upstream_auth_headers(self.config))
            if headers:
                merged_headers.update(headers)
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=req,
                timeout=self.config.timeout_seconds,
                headers=merged_headers,
            ) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", errors="ignore")
                    raise self._map_error(response.status_code, body)
                yield response
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError(str(exc)) from exc
