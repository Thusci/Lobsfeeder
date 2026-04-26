import pytest
from pydantic import ValidationError

from app.core.settings import AppConfig, load_config



def test_settings_reject_duplicate_difficulty(config_data: dict) -> None:
    config_data["routing"]["difficulty_levels"] = ["easy", "easy"]
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config_data)


def test_settings_reject_undefined_model_mapping(config_data: dict) -> None:
    config_data["routing"]["difficulty_to_model"]["hard"] = "missing"
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config_data)


def test_load_config_supports_env_default_syntax(config_data: dict, tmp_path, monkeypatch) -> None:
    config_data["server"]["router_api_keys"] = ["${ROUTER_API_KEY:-}"]
    config_data["server"]["admin_api_keys"] = ["${ADMIN_API_KEY:-admin-default}"]
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
server:
  host: 0.0.0.0
  port: 8080
  request_timeout_seconds: 120
  max_request_body_mb: 8
  router_api_keys:
    - "${ROUTER_API_KEY:-}"
  admin_api_keys:
    - "${ADMIN_API_KEY:-admin-default}"
routing:
  enabled: true
  evaluator_model: model_a
  default_difficulty: medium
  allow_request_override: true
  override_field_mode: alias
  difficulty_levels: [easy, medium, hard, expert]
  difficulty_to_model:
    easy: model_b
    medium: model_c
    hard: model_d
    expert: model_d
models:
  model_a:
    provider: openai_compatible
    base_url: http://upstream-a/v1
    api_key: k-a
    upstream_model_name: judge-model
    limits: {rpm: 10, tpm: 1000, concurrency: 1}
  model_b:
    provider: openai_compatible
    base_url: http://upstream-b/v1
    api_key: k-b
    upstream_model_name: cheap-fast-model
    limits: {rpm: 10, tpm: 1000, concurrency: 1}
  model_c:
    provider: openai_compatible
    base_url: http://upstream-c/v1
    api_key: k-c
    upstream_model_name: balanced-model
    limits: {rpm: 10, tpm: 1000, concurrency: 1}
  model_d:
    provider: openai_compatible
    base_url: http://upstream-d/v1
    api_key: k-d
    upstream_model_name: strongest-model
    limits: {rpm: 10, tpm: 1000, concurrency: 1}
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("ROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    config = load_config(str(config_path))

    assert config.server.router_api_keys == [""]
    assert config.server.admin_api_keys == ["admin-default"]
