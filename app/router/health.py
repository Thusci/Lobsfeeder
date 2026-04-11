from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from app.core.settings import AppConfig


@dataclass
class ModelHealthState:
    failure_count: int = 0
    unhealthy_until: float = 0.0
    last_error: str | None = None


class HealthTracker:
    def __init__(self, config: AppConfig) -> None:
        self._thresholds = {
            model_key: model_cfg.health.failure_threshold
            for model_key, model_cfg in config.models.items()
        }
        self._cooldowns = {
            model_key: float(model_cfg.health.cooldown_seconds)
            for model_key, model_cfg in config.models.items()
        }
        self._states: dict[str, ModelHealthState] = {
            model_key: ModelHealthState() for model_key in config.models
        }

    def is_healthy(self, model_key: str) -> bool:
        state = self._states[model_key]
        now = monotonic()
        if state.unhealthy_until > now:
            return False
        if state.unhealthy_until != 0 and state.unhealthy_until <= now:
            state.unhealthy_until = 0.0
            state.failure_count = 0
        return True

    def record_success(self, model_key: str) -> None:
        state = self._states[model_key]
        state.failure_count = 0
        state.unhealthy_until = 0.0
        state.last_error = None

    def record_failure(self, model_key: str, reason: str) -> None:
        state = self._states[model_key]
        state.failure_count += 1
        state.last_error = reason
        threshold = self._thresholds[model_key]
        if state.failure_count >= threshold:
            state.unhealthy_until = monotonic() + self._cooldowns[model_key]

    def snapshot(self) -> dict[str, dict[str, object]]:
        now = monotonic()
        result: dict[str, dict[str, object]] = {}
        for model_key, state in self._states.items():
            healthy = state.unhealthy_until <= now
            result[model_key] = {
                "healthy": healthy,
                "failure_count": state.failure_count,
                "cooldown_remaining_seconds": max(state.unhealthy_until - now, 0.0),
                "last_error": state.last_error,
            }
        return result

    def healthy_models(self) -> set[str]:
        return {model_key for model_key in self._states if self.is_healthy(model_key)}

    def unhealthy_models_count(self) -> int:
        return len(self._states) - len(self.healthy_models())
