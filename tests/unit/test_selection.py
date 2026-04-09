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
