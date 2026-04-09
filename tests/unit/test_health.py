import time

from app.core.settings import AppConfig
from app.router.health import HealthTracker



def test_health_cooldown_recovery(config_data: dict) -> None:
    config_data["models"]["model_b"]["health"] = {"failure_threshold": 2, "cooldown_seconds": 1}
    config = AppConfig.model_validate(config_data)
    tracker = HealthTracker(config)

    tracker.record_failure("model_b", "timeout")
    assert tracker.is_healthy("model_b") is True

    tracker.record_failure("model_b", "timeout")
    assert tracker.is_healthy("model_b") is False

    time.sleep(1.05)
    assert tracker.is_healthy("model_b") is True
