from __future__ import annotations

import httpx
import pytest

from app.core.access_control import SECRET_PLACEHOLDER
from app.core.settings import AppConfig
from app.main import create_app


@pytest.mark.asyncio
async def test_admin_config_requires_admin_api_key_when_configured(config_data: dict, tmp_path) -> None:
    config_data["server"]["config_source"] = "db"
    config_data["server"]["db_path"] = str(tmp_path / "router.db")
    config_data["server"]["admin_api_keys"] = ["admin-secret"]
    app = create_app(config=AppConfig.model_validate(config_data))

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            unauthorized = await client.get("/admin/config")
            authorized = await client.get("/admin/config", headers={"Authorization": "Bearer admin-secret"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


@pytest.mark.asyncio
async def test_admin_config_falls_back_to_router_api_key_when_admin_keys_empty(config_data: dict, tmp_path) -> None:
    config_data["server"]["config_source"] = "db"
    config_data["server"]["db_path"] = str(tmp_path / "router.db")
    config_data["server"]["router_api_keys"] = ["router-secret"]
    app = create_app(config=AppConfig.model_validate(config_data))

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            authorized = await client.get("/admin/config", headers={"X-API-Key": "router-secret"})

    assert authorized.status_code == 200


@pytest.mark.asyncio
async def test_put_admin_config_returns_400_for_invalid_model_references(config_data: dict, tmp_path) -> None:
    config_data["server"]["config_source"] = "db"
    config_data["server"]["db_path"] = str(tmp_path / "router.db")
    app = create_app(config=AppConfig.model_validate(config_data))

    invalid_payload = {
        **config_data,
        "models": {key: value for key, value in config_data["models"].items() if key != "model_a"},
    }

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/admin/config",
                headers={"Authorization": "Bearer router-secret"},
                json=invalid_payload,
            )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "routing.evaluator_model is not defined in models" in body["error"]["message"]


@pytest.mark.asyncio
async def test_admin_config_redacts_and_preserves_secrets(config_data: dict, tmp_path) -> None:
    config_data["server"]["config_source"] = "db"
    config_data["server"]["db_path"] = str(tmp_path / "router.db")
    config_data["server"]["admin_api_keys"] = ["admin-secret"]
    app = create_app(config=AppConfig.model_validate(config_data))

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/admin/config", headers={"Authorization": "Bearer admin-secret"})
            payload = response.json()["config"]
            assert payload["server"]["router_api_keys"] == [SECRET_PLACEHOLDER]
            assert payload["server"]["admin_api_keys"] == [SECRET_PLACEHOLDER]
            assert payload["models"]["model_a"]["api_key"] == SECRET_PLACEHOLDER

            saved = await client.put(
                "/admin/config",
                headers={"Authorization": "Bearer admin-secret"},
                json=payload,
            )

        assert saved.status_code == 200
        services = app.state.services
        assert services.config.server.router_api_keys == ["router-secret"]
        assert services.config.server.admin_api_keys == ["admin-secret"]
        assert services.config.models["model_a"].api_key == "k-a"


@pytest.mark.asyncio
async def test_admin_config_rejects_public_client_network(config_data: dict, tmp_path) -> None:
    config_data["server"]["config_source"] = "db"
    config_data["server"]["db_path"] = str(tmp_path / "router.db")
    config_data["server"]["admin_api_keys"] = ["admin-secret"]
    app = create_app(config=AppConfig.model_validate(config_data))

    transport = httpx.ASGITransport(app=app, client=("203.0.113.10", 1234))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/admin/config", headers={"Authorization": "Bearer admin-secret"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_network_forbidden"
