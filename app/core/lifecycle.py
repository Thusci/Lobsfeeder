from __future__ import annotations

from dataclasses import dataclass

from app.clients.registry import ClientRegistry
from app.core.settings import AppConfig
from app.evaluator.service import EvaluatorService
from app.ratelimit.estimation import TokenEstimator
from app.ratelimit.manager import RateLimitManager
from app.router.dispatcher import RouterDispatcher
from app.router.health import HealthTracker
from app.telemetry.metrics import MetricsRegistry


@dataclass
class RouterServices:
    config: AppConfig
    clients: ClientRegistry
    metrics: MetricsRegistry
    token_estimator: TokenEstimator
    rate_limits: RateLimitManager
    health: HealthTracker
    evaluator: EvaluatorService
    dispatcher: RouterDispatcher


async def build_services(config: AppConfig) -> RouterServices:
    metrics = MetricsRegistry(enabled=config.telemetry.expose_metrics)
    clients = ClientRegistry(config)
    token_estimator = TokenEstimator(chars_per_token=config.estimation.chars_per_token_fallback)
    rate_limits = RateLimitManager(config)
    health = HealthTracker(config)
    evaluator = EvaluatorService(config=config, clients=clients)
    dispatcher = RouterDispatcher(
        config=config,
        clients=clients,
        metrics=metrics,
        token_estimator=token_estimator,
        rate_limits=rate_limits,
        health=health,
        evaluator=evaluator,
    )
    return RouterServices(
        config=config,
        clients=clients,
        metrics=metrics,
        token_estimator=token_estimator,
        rate_limits=rate_limits,
        health=health,
        evaluator=evaluator,
        dispatcher=dispatcher,
    )


async def close_services(services: RouterServices) -> None:
    await services.clients.aclose_all()
