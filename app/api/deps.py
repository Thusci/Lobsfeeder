from __future__ import annotations

import secrets
from typing import Any

from fastapi import Request

from app.api.schemas import ChatCompletionRequest
from app.core.errors import AuthenticationError, ValidationError
from app.core.lifecycle import RouterServices


def get_services(request: Request) -> RouterServices:
    services = getattr(request.app.state, "services", None)
    if services is None:
        raise ValidationError("Router services are not initialized")
    return services


def enforce_router_auth(request: Request, services: RouterServices) -> None:
    _enforce_api_keys(
        request,
        services.config.server.router_api_keys,
        missing_message="Missing API key. Use Authorization: Bearer <key>, X-API-Key, or api-key.",
        invalid_message="Invalid router API key",
    )


def enforce_admin_auth(request: Request, services: RouterServices) -> None:
    admin_keys = services.config.server.admin_api_keys or services.config.server.router_api_keys
    _enforce_api_keys(
        request,
        admin_keys,
        missing_message="Missing admin API key. Use Authorization: Bearer <key>, X-API-Key, or api-key.",
        invalid_message="Invalid admin API key",
    )


def validate_request_limits(body: ChatCompletionRequest, services: RouterServices) -> None:
    limits = services.config.server

    if len(body.messages) > limits.max_messages:
        raise ValidationError(f"messages count exceeds max_messages={limits.max_messages}")

    tools = body.tools or []
    if len(tools) > limits.max_tools:
        raise ValidationError(f"tools count exceeds max_tools={limits.max_tools}")

    stop = body.stop
    if isinstance(stop, list) and len(stop) > limits.max_stop_sequences:
        raise ValidationError(f"stop count exceeds max_stop_sequences={limits.max_stop_sequences}")

    message_chars = 0
    for message in body.messages:
        message_chars += _content_length(message.get("content"))
    if message_chars > limits.max_message_chars:
        raise ValidationError(f"message content exceeds max_message_chars={limits.max_message_chars}")

    tool_chars = sum(len(str(tool)) for tool in tools)
    if tool_chars > limits.max_tool_definition_chars:
        raise ValidationError(
            f"tool definitions exceed max_tool_definition_chars={limits.max_tool_definition_chars}"
        )


def _content_length(content: Any) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(str(item)) for item in content)
    if content is None:
        return 0
    return len(str(content))


def _extract_router_api_key(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth:
        scheme, _, credentials = auth.partition(" ")
        if scheme.lower() == "bearer" and credentials.strip():
            return credentials.strip()

    for header_name in ("x-api-key", "api-key"):
        value = request.headers.get(header_name)
        if value and value.strip():
            return value.strip()

    return None


def _enforce_api_keys(
    request: Request,
    keys: list[str],
    *,
    missing_message: str,
    invalid_message: str,
) -> None:
    normalized_keys = [key.strip() for key in keys if key.strip()]
    if not normalized_keys:
        raise AuthenticationError(missing_message)

    token = _extract_router_api_key(request)
    if token is None:
        raise AuthenticationError(missing_message)

    if not any(secrets.compare_digest(token, key) for key in normalized_keys):
        raise AuthenticationError(invalid_message)
