from __future__ import annotations

import logging
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError as PydanticValidationError

from app.api.routes_admin import router as admin_router
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.schemas import make_openai_error
from app.core.access_control import is_admin_path, is_host_allowed, request_client_host
from app.core.errors import RouterError, ValidationError
from app.core.config_store import ConfigStore
from app.core.lifecycle import RouterServices, build_services, close_services
from app.core.logging import configure_logging
from app.core.settings import AppConfig, load_config


logger = logging.getLogger(__name__)


def create_app(config: AppConfig | None = None, config_path: str | None = None) -> FastAPI:
    app_config = config or load_config(config_path)
    config_store: ConfigStore | None = None
    config_runtime = {
        "requested_source": app_config.server.config_source,
        "active_source": app_config.server.config_source,
        "startup_warning": None,
        "stored_updated_at": None,
    }
    if app_config.server.config_source == "db":
        config_store = ConfigStore(app_config.server.db_path)
        stored = config_store.get_config()
        if stored is None:
            config_store.set_config(app_config.model_dump())
            config_runtime["stored_updated_at"] = None
        else:
            config_runtime["stored_updated_at"] = stored.updated_at
            try:
                app_config = AppConfig.model_validate(stored.payload)
            except PydanticValidationError as exc:
                warning = (
                    "Stored DB config is invalid; using file config until you fix and save a valid config from the UI. "
                    f"Validation error: {exc}"
                )
                logger.warning(warning)
                config_runtime["active_source"] = "file-fallback"
                config_runtime["startup_warning"] = warning
    configure_logging(level=app_config.telemetry.log_level, structured=app_config.telemetry.structured_logs)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        services: RouterServices = await build_services(app_config)
        app.state.services = services
        app.state.config_store = config_store
        app.state.config_lock = asyncio.Lock()
        app.state.config_runtime = config_runtime
        _log_access_policy(app_config)
        try:
            yield
        finally:
            await close_services(services)

    app = FastAPI(title="Lobsfeeder", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_timeout(request: Request, call_next):
        services: RouterServices | None = getattr(request.app.state, "services", None)
        if services is None:
            return _router_error_response(
                RouterError(
                    message="Router services are not initialized",
                    status_code=503,
                    error_type="server_error",
                    code="services_not_initialized",
                    retryable=True,
                )
            )
        try:
            return await asyncio.wait_for(call_next(request), timeout=services.config.server.request_timeout_seconds)
        except asyncio.TimeoutError:
            return _router_error_response(
                RouterError(
                    message="Request timed out",
                    status_code=504,
                    error_type="server_error",
                    code="request_timeout",
                    retryable=True,
                )
            )

    @app.middleware("http")
    async def admin_network_guard(request: Request, call_next):
        services: RouterServices | None = getattr(request.app.state, "services", None)
        if services is None:
            return _router_error_response(
                RouterError(
                    message="Router services are not initialized",
                    status_code=503,
                    error_type="server_error",
                    code="services_not_initialized",
                    retryable=True,
                )
            )
        if is_admin_path(request.url.path):
            client_host = request_client_host(request)
            allowed = is_host_allowed(client_host, services.config.server.admin_allowed_cidrs)
            if not allowed:
                return _router_error_response(
                    RouterError(
                        message="Admin UI and config APIs are restricted to configured private networks",
                        status_code=403,
                        error_type="authentication_error",
                        code="admin_network_forbidden",
                        retryable=False,
                    )
                )
        return await call_next(request)

    @app.middleware("http")
    async def body_size_limit(request: Request, call_next):
        services: RouterServices | None = getattr(request.app.state, "services", None)
        if services is None:
            return _router_error_response(
                RouterError(
                    message="Router services are not initialized",
                    status_code=503,
                    error_type="server_error",
                    code="services_not_initialized",
                    retryable=True,
                )
            )
        max_bytes = services.config.server.max_request_body_mb * 1024 * 1024
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError:
                return _router_error_response(ValidationError("Invalid Content-Length header"))
            if declared_size > max_bytes:
                return _router_error_response(ValidationError("Request body too large"))

        received = 0
        original_receive = request._receive

        async def limited_receive():
            nonlocal received
            message = await original_receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"") or b""
                received += len(body)
                if received > max_bytes:
                    raise ValidationError("Request body too large")
            return message

        request._receive = limited_receive
        return await call_next(request)

    @app.middleware("http")
    async def body_size_limit_error_adapter(request: Request, call_next):
        try:
            return await call_next(request)
        except ValidationError as exc:
            return _router_error_response(exc)

    @app.exception_handler(RouterError)
    async def router_error_handler(_: Request, exc: RouterError) -> JSONResponse:
        return _router_error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = make_openai_error(str(exc), "invalid_request_error", "validation_error")
        return JSONResponse(status_code=400, content=payload)

    @app.exception_handler(Exception)
    async def generic_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled exception: %s", exc)
        payload = make_openai_error("Internal server error", "server_error", "internal_error")
        return JSONResponse(status_code=500, content=payload)

    app.include_router(chat_router)
    app.include_router(health_router)
    app.include_router(admin_router)
    app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")
    return app


def _router_error_response(exc: RouterError) -> JSONResponse:
    payload = make_openai_error(exc.message, exc.error_type, exc.code)
    return JSONResponse(status_code=exc.status_code, content=payload)


def _log_access_policy(config: AppConfig) -> None:
    router_keys = [key for key in config.server.router_api_keys if key.strip()]
    admin_keys = [key for key in config.server.admin_api_keys if key.strip()]
    effective_admin_keys = admin_keys or router_keys

    logger.info(
        "access policy: router_auth=%s admin_auth=%s admin_allowed_cidrs=%s",
        "configured" if router_keys else "missing",
        "configured" if effective_admin_keys else "missing",
        ",".join(config.server.admin_allowed_cidrs),
    )
    logger.info(
        "admin UI and /admin/* are only served to clients inside admin_allowed_cidrs; do not expose them directly to the public internet"
    )
    if config.server.host == "0.0.0.0":
        logger.warning(
            "server.host is 0.0.0.0; keep firewall/reverse-proxy rules aligned with admin_allowed_cidrs"
        )
    if not router_keys:
        logger.warning("router_api_keys is empty; router endpoints other than /healthz will reject requests")
    if not effective_admin_keys:
        logger.warning("admin_api_keys/router_api_keys are empty; /ui config actions and /admin/* will reject requests")


def _create_default_app() -> FastAPI:
    try:
        return create_app()
    except Exception as exc:  # pragma: no cover
        logger.exception("failed to create default app: %s", exc)
        app = FastAPI(title="Lobsfeeder", version="0.1.0")

        @app.get("/healthz")
        async def healthz_failed() -> JSONResponse:
            payload = make_openai_error("Application startup failed", "server_error", "startup_failure")
            return JSONResponse(status_code=503, content=payload)

        return app


app = _create_default_app()
