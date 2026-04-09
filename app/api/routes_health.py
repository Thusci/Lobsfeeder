from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.api.deps import enforce_router_auth, get_services
from app.core.errors import UpstreamClientError


router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> tuple[dict[str, object], int] | dict[str, object]:
    services = get_services(request)
    ready = bool(services.config.models)
    payload = {"ready": ready, "models": len(services.config.models)}
    if ready:
        return payload
    raise UpstreamClientError("Router not ready", status_code=503)


@router.get("/metrics")
async def metrics(request: Request) -> PlainTextResponse:
    services = get_services(request)
    if not services.config.telemetry.expose_metrics:
        raise UpstreamClientError("Metrics endpoint is disabled", status_code=404)
    return PlainTextResponse(services.metrics.render_prometheus(), media_type="text/plain")


@router.get("/debug/models")
async def debug_models(request: Request) -> dict[str, object]:
    services = get_services(request)
    enforce_router_auth(request, services)
    health = services.health.snapshot()
    limits = await services.rate_limits.snapshot()
    return {
        "health": health,
        "limits": limits,
    }
