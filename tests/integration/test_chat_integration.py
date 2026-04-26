from __future__ import annotations

import asyncio
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
async def router_client(app_config, auth: bool = True):
    app = create_app(config=app_config)
    services = await build_services(app_config)
    app.state.services = services
    transport = httpx.ASGITransport(app=app)
    headers = {}
    if auth and app_config.server.router_api_keys:
        headers["Authorization"] = f"Bearer {app_config.server.router_api_keys[0]}"
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
            yield client
    finally:
        await close_services(services)


@asynccontextmanager
async def router_client_with_services(app_config, auth: bool = True):
    app = create_app(config=app_config)
    services = await build_services(app_config)
    app.state.services = services
    transport = httpx.ASGITransport(app=app)
    headers = {}
    if auth and app_config.server.router_api_keys:
        headers["Authorization"] = f"Bearer {app_config.server.router_api_keys[0]}"
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
            yield client, services
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

    async with router_client(app_config, auth=False) as client:
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "force:model_b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_router_auth_accepts_x_api_key_header(app_config, respx_mock) -> None:
    app_config.server.router_api_keys = ["secret"]
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            headers={"X-API-Key": "secret"},
            json={"model": "force:model_b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_router_auth_accepts_api_key_header(app_config, respx_mock) -> None:
    app_config.server.router_api_keys = ["secret"]
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        resp = await client.post(
            "/v1/chat/completions",
            headers={"api-key": "secret"},
            json={"model": "force:model_b", "messages": [{"role": "user", "content": "hi"}]},
        )

    assert resp.status_code == 200


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


@pytest.mark.asyncio
async def test_reject_strategy_returns_429_without_fallback(app_config, respx_mock) -> None:
    app_config.routing.fallback_policy.strategy = "reject"
    app_config.models["model_b"].limits.rpm = 1

    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        first = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi"}]},
        )
        second = await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "again"}]},
        )

    assert first.status_code == 200
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_queue_strategy_waits_for_capacity(app_config, respx_mock) -> None:
    app_config.routing.fallback_policy.strategy = "queue"
    app_config.routing.fallback_policy.queue_wait_ms = 300
    app_config.routing.fallback_policy.queue_poll_interval_ms = 10
    app_config.models["model_b"].limits.concurrency = 1

    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client_with_services(app_config) as pair:
        client, services = pair
        held_lease = await services.rate_limits.acquire("model_b", estimated_tokens=1)

        async def release_later() -> None:
            await asyncio.sleep(0.05)
            await held_lease.finalize(actual_tokens=1)

        release_task = asyncio.create_task(release_later())
        try:
            resp = await client.post(
                "/v1/chat/completions",
                json={"model": "auto", "messages": [{"role": "user", "content": "queued"}]},
            )
        finally:
            await release_task

    assert resp.status_code == 200
    assert resp.headers["x-selected-model"] == "model_b"


@pytest.mark.asyncio
async def test_readyz_reflects_internal_state(app_config) -> None:
    async with router_client_with_services(app_config) as pair:
        client, services = pair
        for model_key in ("model_b", "model_c", "model_d"):
            services.health.record_failure(model_key, "test")
            services.health.record_failure(model_key, "test")

        resp = await client.get("/readyz")

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_metrics_exposes_operational_gauges(app_config, respx_mock) -> None:
    _mock_upstream(respx_mock, "upstream-a", httpx.Response(200, json=EVALUATOR_OK))
    _mock_upstream(respx_mock, "upstream-b", httpx.Response(200, json=_chat_ok()))

    async with router_client(app_config) as client:
        await client.post(
            "/v1/chat/completions",
            json={"model": "auto", "messages": [{"role": "user", "content": "hi"}]},
        )
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    assert "current_per_model_concurrency" in resp.text
    assert "unhealthy_models_count" in resp.text


@pytest.mark.asyncio
async def test_health_and_metrics_require_router_api_key_when_configured(app_config) -> None:
    app_config.server.router_api_keys = ["secret"]

    async with router_client(app_config, auth=False) as client:
        health = await client.get("/healthz")
        ready = await client.get("/readyz")
        metrics = await client.get("/metrics")
        authorized = await client.get("/healthz", headers={"Authorization": "Bearer secret"})

    assert health.status_code == 200
    assert ready.status_code == 401
    assert metrics.status_code == 401
    assert authorized.status_code == 200
