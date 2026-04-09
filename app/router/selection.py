from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import AppConfig


@dataclass
class RouteMode:
    mode: str
    override_model: str | None
    error_message: str | None = None



def resolve_route_mode(request_model: str, config: AppConfig) -> RouteMode:
    routing = config.routing
    if request_model.startswith("force:"):
        forced = request_model.split(":", 1)[1].strip()
        if not forced or forced not in config.models:
            return RouteMode(
                mode="invalid_override",
                override_model=None,
                error_message=f"Unknown forced model override: {forced or '<empty>'}",
            )
        return RouteMode(mode="bypass", override_model=forced)

    if routing.allow_request_override and request_model in config.models:
        return RouteMode(mode="bypass", override_model=request_model)

    if not routing.enabled:
        if request_model in config.models:
            return RouteMode(mode="bypass", override_model=request_model)
        return RouteMode(mode="evaluated", override_model=None)

    return RouteMode(mode="evaluated", override_model=None)
