from app.core.settings import AppConfig
from app.router.selection import resolve_route_mode



def test_force_override_unknown_model(config_data: dict) -> None:
    config = AppConfig.model_validate(config_data)
    mode = resolve_route_mode("force:unknown", config)
    assert mode.mode == "invalid_override"


def test_direct_internal_model_bypasses(config_data: dict) -> None:
    config = AppConfig.model_validate(config_data)
    mode = resolve_route_mode("model_b", config)
    assert mode.mode == "bypass"
    assert mode.override_model == "model_b"


def test_force_override_respects_disabled_override(config_data: dict) -> None:
    config_data["routing"]["allow_request_override"] = False
    config = AppConfig.model_validate(config_data)

    mode = resolve_route_mode("force:model_b", config)

    assert mode.mode == "invalid_override"
    assert mode.error_message == "Model override is disabled"


def test_force_only_mode_rejects_alias_override(config_data: dict) -> None:
    config_data["routing"]["override_field_mode"] = "force_only"
    config = AppConfig.model_validate(config_data)

    alias_mode = resolve_route_mode("model_b", config)
    force_mode = resolve_route_mode("force:model_b", config)

    assert alias_mode.mode == "evaluated"
    assert force_mode.mode == "bypass"
