from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[dict[str, Any]]
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    user: str | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not value:
            raise ValueError("messages must not be empty")
        for msg in value:
            if "role" not in msg:
                raise ValueError("each message must include role")
            if "content" not in msg:
                raise ValueError("each message must include content")
        return value


class OpenAIErrorBody(BaseModel):
    message: str
    type: str
    code: str | None = None


class OpenAIErrorResponse(BaseModel):
    error: OpenAIErrorBody


def make_openai_error(message: str, error_type: str, code: str | None) -> dict[str, Any]:
    body = OpenAIErrorResponse(error=OpenAIErrorBody(message=message, type=error_type, code=code))
    return body.model_dump(exclude_none=True)
