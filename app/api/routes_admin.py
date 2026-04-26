from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import ValidationError as PydanticValidationError

from app.api.deps import enforce_admin_auth, get_services
from app.core.access_control import merge_redacted_secrets, redact_config
from app.core.config_store import ConfigStore
from app.core.errors import ValidationError
from app.core.lifecycle import build_services, close_services
from app.core.settings import AppConfig


router = APIRouter(tags=["admin"])


@router.get("/admin/config")
async def get_config(request: Request) -> dict[str, object]:
    services = get_services(request)
    enforce_admin_auth(request, services)
    config_store: ConfigStore | None = getattr(request.app.state, "config_store", None)
    runtime = getattr(request.app.state, "config_runtime", {}) or {}
    requested_source = runtime.get("requested_source", services.config.server.config_source)
    active_source = runtime.get("active_source", services.config.server.config_source)
    writable = requested_source == "db" and config_store is not None
    if writable:
        stored = config_store.get_config()
        return {
            "source": active_source,
            "writable": True,
            "startup_warning": runtime.get("startup_warning"),
            "updated_at": stored.updated_at if stored else None,
            "config": redact_config(services.config),
        }
    return {
        "source": active_source,
        "writable": False,
        "startup_warning": runtime.get("startup_warning"),
        "config": redact_config(services.config),
    }


@router.post("/admin/config/validate")
async def validate_config(request: Request) -> dict[str, object]:
    services = get_services(request)
    enforce_admin_auth(request, services)
    payload = merge_redacted_secrets(await request.json(), services.config)
    try:
        AppConfig.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc
    return {"valid": True}


@router.put("/admin/config")
async def update_config(request: Request) -> dict[str, object]:
    services = get_services(request)
    enforce_admin_auth(request, services)
    if services.config.server.config_source != "db":
        raise ValidationError("config_source is not set to db; updates are disabled")
    config_store: ConfigStore | None = getattr(request.app.state, "config_store", None)
    if config_store is None:
        raise ValidationError("Config store is not initialized")

    payload = merge_redacted_secrets(await request.json(), services.config)
    try:
        new_config = AppConfig.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc
    lock = getattr(request.app.state, "config_lock", None)
    if lock is None:
        raise ValidationError("Config lock is not initialized")

    async with lock:
        new_services = await build_services(new_config)
        old_services = request.app.state.services
        request.app.state.services = new_services
        config_store.set_config(new_config.model_dump())
        request.app.state.config_runtime = {
            "requested_source": "db",
            "active_source": "db",
            "startup_warning": None,
            "stored_updated_at": None,
        }
        await close_services(old_services)

    return {"status": "ok"}
