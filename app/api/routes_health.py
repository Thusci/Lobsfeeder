from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.api.deps import enforce_router_auth, get_services
from app.core.errors import UpstreamClientError
from app.router.fallback import build_candidates


router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> tuple[dict[str, object], int] | dict[str, object]:
    services = get_services(request)
    serving_models = _serving_models(request)
    healthy_models = sorted(model_key for model_key in serving_models if services.health.is_healthy(model_key))
    ready = bool(services.config.models) and bool(serving_models) and bool(healthy_models)
    payload = {
        "ready": ready,
        "models": len(services.config.models),
        "serving_models": sorted(serving_models),
        "healthy_serving_models": healthy_models,
    }
    if ready:
        return payload
    raise UpstreamClientError("Router not ready", status_code=503)


@router.get("/metrics")
async def metrics(request: Request) -> PlainTextResponse:
    services = get_services(request)
    if not services.config.telemetry.expose_metrics:
        raise UpstreamClientError("Metrics endpoint is disabled", status_code=404)
    health = services.health.snapshot()
    limits = await services.rate_limits.snapshot()
    global_limits = await services.rate_limits.global_snapshot()
    for model_key, values in limits.items():
        services.metrics.set_gauge(
            "current_per_model_concurrency",
            float(values["concurrency"]),
            {"model": model_key},
        )
        services.metrics.set_gauge(
            "current_per_model_rpm_window",
            float(values["rpm_in_window"]),
            {"model": model_key},
        )
        services.metrics.set_gauge(
            "current_per_model_tpm_window",
            float(values["tpm_in_window"]),
            {"model": model_key},
        )
        services.metrics.set_gauge(
            "model_health_status",
            1.0 if health[model_key]["healthy"] else 0.0,
            {"model": model_key},
        )
    services.metrics.set_gauge("unhealthy_models_count", float(services.health.unhealthy_models_count()))
    if global_limits["rpm_in_window"] is not None:
        services.metrics.set_gauge("current_global_rpm_window", float(global_limits["rpm_in_window"]))
    if global_limits["concurrency"] is not None:
        services.metrics.set_gauge("current_global_concurrency", float(global_limits["concurrency"]))
    return PlainTextResponse(services.metrics.render_prometheus(), media_type="text/plain")


@router.get("/debug/models")
async def debug_models(request: Request) -> dict[str, object]:
    services = get_services(request)
    enforce_router_auth(request, services)
    health = services.health.snapshot()
    limits = await services.rate_limits.snapshot()
    global_limits = await services.rate_limits.global_snapshot()
    return {
        "health": health,
        "limits": limits,
        "global_limits": global_limits,
    }


def _serving_models(request: Request) -> set[str]:
    services = get_services(request)
    config = services.config
    if not config.routing.enabled:
        return set(config.models.keys())

    serving_models: set[str] = set()
    for difficulty in config.routing.difficulty_levels:
        serving_models.update(build_candidates(config, difficulty=difficulty))
    return serving_models
