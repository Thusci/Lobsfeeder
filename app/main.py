from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.schemas import make_openai_error
from app.core.errors import RouterError, ValidationError
from app.core.lifecycle import RouterServices, build_services, close_services
from app.core.logging import configure_logging
from app.core.settings import AppConfig, load_config


logger = logging.getLogger(__name__)


def create_app(config: AppConfig | None = None, config_path: str | None = None) -> FastAPI:
    app_config = config or load_config(config_path)
    configure_logging(level=app_config.telemetry.log_level, structured=app_config.telemetry.structured_logs)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        services: RouterServices = await build_services(app_config)
        app.state.services = services
        try:
            yield
        finally:
            await close_services(services)

    app = FastAPI(title="openclaw-ai-router", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def body_size_limit(request: Request, call_next):
        services: RouterServices = request.app.state.services
        max_bytes = services.config.server.max_request_body_mb * 1024 * 1024
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_bytes:
            raise ValidationError("Request body too large")
        return await call_next(request)

    @app.exception_handler(RouterError)
    async def router_error_handler(_: Request, exc: RouterError) -> JSONResponse:
        payload = make_openai_error(exc.message, exc.error_type, exc.code)
        return JSONResponse(status_code=exc.status_code, content=payload)

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
    return app


app = create_app()
