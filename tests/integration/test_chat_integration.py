from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import pytest

from app.core.lifecycle import build_services, close_services
from app.main import create_app


EVALUATOR_OK = {
    "id": "eval-1",
    "object": "chat.completion",
    "created": 1,
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": '{"difficulty":"easy"}'},
            "finish_reason": "stop",
        }
    ],
}


def _chat_ok(model_name: str = "cheap-fast-model") -> dict:
    return {
        "id": "chat-1",
        "object": "chat.completion",
        "created": 1,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "hello"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
    }


def _mock_upstream(respx_mock, host: str, response: httpx.Response | Exception):
    route = respx_mock.post(url__regex=rf"^http://{host}(/v1)?/chat/completions/?$")
    if isinstance(response, Exception):
        return route.mock(side_effect=response)
    return route.mock(return_value=response)


@asynccontextmanager
async def router_client(app_config):
    app = create_app(config=app_config)
    services = await build_services(app_config)
    app.state.services = services
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        await close_services(services)


@pytest.mark.asyncio
async def test_evaluated_route_success_model_b(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200
    assert resp.json()["model"] == "model_b"


@pytest.mark.asyncio
async def test_evaluator_timeout_falls_back_default(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.ReadTimeout("timeout"))
    _mock_upstream(respx_mock, "upstream-c", httpx.Response(200, json=_chat_ok("balanced-model")))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200
    assert resp.json()["model"] == "model_c"


@pytest.mark.asyncio
async def test_primary_429_fallback_next_model(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(429, json={"error": "busy"}))
    _mock_upstream(respx_mock, "upstream-c", httpx.Response(200, json=_chat_ok("balanced-model")))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200
    assert resp.json()["model"] == "model_c"


@pytest.mark.asyncio
async def test_all_candidates_fail_returns_503(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(500, text="boom"))
    _mock_upstream(respx_mock, "upstream-c", httpx.Response(500, text="boom"))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_bypass_route_works(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "model_b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200
    assert resp.headers["x-route-mode"] == "bypass"


@pytest.mark.asyncio
async def test_force_override_marks_bypass_route_mode(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "force:model_b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200
    assert resp.headers["x-route-mode"] == "bypass"


@pytest.mark.asyncio
async def test_unknown_override_returns_400(app_config) -> None:
    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "force:missing", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_router_auth_returns_401(app_config) -> None:
    app_config.server.router_api_keys = ["secret"]

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "force:model_b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stream_passthrough(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(
        respx_mock,
        "upstream-b",
        httpx.Response(
            200,
            content=b"data: {\"id\":\"evt1\"}\n\ndata: [DONE]\n\n",
            headers={"content-type": "text/event-stream"},
        ),
    )

    async with router_client(app_config) as client:
        async with client.stream(
            "POST",
            "/v1/chat/completions",
            json={"model": "auto", "stream": True, "messages": [{"role": "user", "content": "hi"}]},
        ) as resp:
            body = (await resp.aread()).decode("utf-8")

    assert resp.status_code == 200
    assert "[DONE]" in body


@pytest.mark.asyncio
async def test_stream_first_target_failure_before_first_chunk_fallback(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(500, text="boom"))
    _mock_upstream(
        respx_mock,
        "upstream-c",
        httpx.Response(
            200,
            content=b"data: {\"id\":\"evt2\"}\n\ndata: [DONE]\n\n",
            headers={"content-type": "text/event-stream"},
        ),
    )

    async with router_client(app_config) as client:
        async with client.stream(
            "POST",
            "/v1/chat/completions",
            json={"model": "auto", "stream": True, "messages": [{"role": "user", "content": "hi"}]},
        ) as resp:
            body = (await resp.aread()).decode("utf-8")

    assert resp.status_code == 200
    assert resp.headers["x-selected-model"] == "model_c"
    assert "[DONE]" in body
