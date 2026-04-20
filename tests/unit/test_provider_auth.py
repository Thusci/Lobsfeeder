import json

import pytest

from app.clients.auth import build_upstream_auth_headers
from app.core.errors import UpstreamAuthError
from app.core.settings import ModelConfig


def _base_limits() -> dict:
    return {"rpm": 10, "tpm": 1000, "concurrency": 1}


def test_build_upstream_auth_headers_defaults_to_bearer_for_openai_compatible() -> None:
    config = ModelConfig.model_validate(
        {
            "provider": "openai_compatible",
            "provider_group": "openai",
            "base_url": "https://example.com/v1",
            "api_key": "test-key",
            "upstream_model_name": "gpt-test",
            "limits": _base_limits(),
        }
    )

    headers = build_upstream_auth_headers(config)

    assert headers == {"Authorization": "Bearer test-key"}


def test_build_upstream_auth_headers_supports_custom_api_key_header() -> None:
    config = ModelConfig.model_validate(
        {
            "provider": "openai_compatible",
            "provider_group": "azure-openai",
            "base_url": "https://example.com/openai/deployments/test",
            "api_key": "azure-key",
            "api_key_header": "api-key",
            "api_key_prefix": "",
            "upstream_model_name": "gpt-4.1-mini",
            "limits": _base_limits(),
        }
    )

    headers = build_upstream_auth_headers(config)

    assert headers == {"api-key": "azure-key"}


def test_build_upstream_auth_headers_supports_codex_oauth(tmp_path) -> None:
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(
        json.dumps({"tokens": {"access_token": "oauth-token"}}),
        encoding="utf-8",
    )
    config = ModelConfig.model_validate(
        {
            "provider": "openai-codex-oauth",
            "provider_group": "openai",
            "base_url": "https://api.openai.com/v1",
            "oauth_token_path": str(auth_path),
            "upstream_model_name": "gpt-5.1-codex",
            "limits": _base_limits(),
        }
    )

    headers = build_upstream_auth_headers(config)

    assert headers["Authorization"] == "Bearer oauth-token"


def test_build_upstream_auth_headers_rejects_missing_codex_oauth_token(tmp_path) -> None:
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(json.dumps({"tokens": {}}), encoding="utf-8")
    config = ModelConfig.model_validate(
        {
            "provider": "openai-codex-oauth",
            "provider_group": "openai",
            "base_url": "https://api.openai.com/v1",
            "oauth_token_path": str(auth_path),
            "upstream_model_name": "gpt-5.1-codex",
            "limits": _base_limits(),
        }
    )

    with pytest.raises(UpstreamAuthError):
        build_upstream_auth_headers(config)
