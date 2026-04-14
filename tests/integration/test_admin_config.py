from __future__ import annotations

import httpx
import pytest

from app.core.settings import AppConfig
from app.main import create_app


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
            response = await client.put("/admin/config", json=invalid_payload)

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "routing.evaluator_model is not defined in models" in body["error"]["message"]
