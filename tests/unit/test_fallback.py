from app.core.settings import AppConfig
from app.router.fallback import build_candidates



def test_build_candidates_dedupes_and_respects_hops(config_data: dict) -> None:
    config_data["routing"]["fallback_policy"]["ordered_candidates"]["easy"] = ["model_b", "model_c", "model_b", "model_d"]
    config_data["routing"]["fallback_policy"]["max_fallback_hops"] = 1
    config = AppConfig.model_validate(config_data)

    candidates = build_candidates(config, difficulty="easy", override_model=None)
    assert candidates == ["model_b", "model_c"]


def test_build_candidates_excludes_evaluator_if_disabled(config_data: dict) -> None:
    config_data["routing"]["difficulty_to_model"]["easy"] = "model_a"
    config_data["routing"]["allow_evaluator_as_candidate"] = False
    config = AppConfig.model_validate(config_data)

    candidates = build_candidates(config, difficulty="easy", override_model=None)
    assert "model_a" not in candidates
