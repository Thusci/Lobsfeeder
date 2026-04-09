from __future__ import annotations

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
    keys = services.config.server.router_api_keys
    if not keys:
        return

    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = auth.removeprefix("Bearer ").strip()
    if token not in keys:
        raise AuthenticationError("Invalid router API key")


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
