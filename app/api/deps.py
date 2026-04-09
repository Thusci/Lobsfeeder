from __future__ import annotations

from fastapi import Request

from app.core.errors import UpstreamClientError
from app.core.lifecycle import RouterServices



def get_services(request: Request) -> RouterServices:
    return request.app.state.services


def enforce_router_auth(request: Request, services: RouterServices) -> None:
    keys = services.config.server.router_api_keys
    if not keys:
        return

    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise UpstreamClientError("Missing or invalid Authorization header", status_code=401)

    token = auth.removeprefix("Bearer ").strip()
    if token not in keys:
        raise UpstreamClientError("Invalid router API key", status_code=401)
