import pytest
from pydantic import ValidationError

from app.core.settings import AppConfig



def test_settings_reject_duplicate_difficulty(config_data: dict) -> None:
    config_data["routing"]["difficulty_levels"] = ["easy", "easy"]
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config_data)


def test_settings_reject_undefined_model_mapping(config_data: dict) -> None:
    config_data["routing"]["difficulty_to_model"]["hard"] = "missing"
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config_data)
