from __future__ import annotations

import json

import httpx
import pytest

from app.main import create_app


@pytest.mark.asyncio
async def test_codex_oauth_provider_uses_access_token(app_config, respx_mock, tmp_path) -> None:
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(
        json.dumps({"tokens": {"access_token": "oauth-token"}}),
        encoding="utf-8",
    )
    app_config.models["model_b"].provider = "openai-codex-oauth"
    app_config.models["model_b"].provider_group = "openai"
    app_config.models["model_b"].oauth_token_path = str(auth_path)
    app_config.models["model_b"].api_key = None
    app_config.routing.enabled = False

    seen_auth = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_auth["authorization"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={
                "id": "chat-1",
                "object": "chat.completion",
                "created": 1,
                "model": "gpt-5.1-codex",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hello"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )

    respx_mock.post(url__regex=r"^http://upstream-b(/v1)?/chat/completions/?$").mock(side_effect=handler)

    app = create_app(config=app_config)
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": "Bearer router-secret"},
                    json={"model": "model_b", "messages": [{"role": "user", "content": "hi"}]},
                )

    assert response.status_code == 200
    assert seen_auth["authorization"] == "Bearer oauth-token"
