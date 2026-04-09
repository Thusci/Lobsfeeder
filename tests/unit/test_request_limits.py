from types import SimpleNamespace

import pytest

from app.api.deps import validate_request_limits
from app.api.schemas import ChatCompletionRequest
from app.core.errors import ValidationError
from app.core.settings import AppConfig


def test_validate_request_limits_rejects_too_many_messages(config_data: dict) -> None:
    config_data["server"]["max_messages"] = 1
    config = AppConfig.model_validate(config_data)
    services = SimpleNamespace(config=config)
    body = ChatCompletionRequest.model_validate(
        {
            "model": "auto",
            "messages": [
                {"role": "user", "content": "a"},
                {"role": "assistant", "content": "b"},
            ],
        }
    )

    with pytest.raises(ValidationError):
        validate_request_limits(body, services)


def test_validate_request_limits_rejects_large_tool_payload(config_data: dict) -> None:
    config_data["server"]["max_tool_definition_chars"] = 10
    config = AppConfig.model_validate(config_data)
    services = SimpleNamespace(config=config)
    body = ChatCompletionRequest.model_validate(
        {
            "model": "auto",
            "messages": [{"role": "user", "content": "a"}],
            "tools": [{"type": "function", "function": {"name": "tool", "description": "0123456789ABC"}}],
        }
    )

    with pytest.raises(ValidationError):
        validate_request_limits(body, services)
