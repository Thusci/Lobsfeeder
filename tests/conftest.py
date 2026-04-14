from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

import pytest

from app.core.settings import AppConfig

os.environ.setdefault("MODEL_A_API_KEY", "test-a")
os.environ.setdefault("MODEL_B_API_KEY", "test-b")
os.environ.setdefault("MODEL_C_API_KEY", "test-c")
os.environ.setdefault("MODEL_D_API_KEY", "test-d")



def build_base_config() -> dict[str, Any]:
    return {
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "request_timeout_seconds": 120,
            "max_request_body_mb": 8,
            "router_api_keys": [],
        },
        "routing": {
            "enabled": True,
            "evaluator_model": "model_a",
            "default_difficulty": "medium",
            "allow_request_override": True,
            "override_field_mode": "alias",
            "difficulty_levels": ["easy", "medium", "hard", "expert"],
            "difficulty_to_model": {
                "easy": "model_b",
                "medium": "model_c",
                "hard": "model_d",
                "expert": "model_d",
            },
            "fallback_policy": {
                "strategy": "fallback",
                "ordered_candidates": {
                    "easy": ["model_b", "model_c"],
                    "medium": ["model_c", "model_d"],
                    "hard": ["model_d"],
                    "expert": ["model_d"],
                },
                "max_fallback_hops": 2,
                "on_evaluator_error_use_default_difficulty": True,
            },
            "strict_mode": False,
            "allow_evaluator_as_candidate": False,
        },
        "models": {
            "model_a": {
                "provider": "openai_compatible",
                "provider_group": "openai",
                "base_url": "http://upstream-a/v1",
                "api_key": "k-a",
                "upstream_model_name": "judge-model",
                "timeout_seconds": 10,
                "retry": {
                    "max_attempts": 1,
                    "backoff_initial_ms": 1,
                    "backoff_max_ms": 5,
                },
                "limits": {"rpm": 100, "tpm": 100000, "concurrency": 5},
                "health": {"failure_threshold": 2, "cooldown_seconds": 1},
            },
            "model_b": {
                "provider": "openai_compatible",
                "provider_group": "openai",
                "base_url": "http://upstream-b/v1",
                "api_key": "k-b",
                "upstream_model_name": "cheap-fast-model",
                "timeout_seconds": 10,
                "retry": {
                    "max_attempts": 1,
                    "backoff_initial_ms": 1,
                    "backoff_max_ms": 5,
                },
                "limits": {"rpm": 100, "tpm": 100000, "concurrency": 5},
                "health": {"failure_threshold": 2, "cooldown_seconds": 1},
            },
            "model_c": {
                "provider": "openai_compatible",
                "provider_group": "openai",
                "base_url": "http://upstream-c/v1",
                "api_key": "k-c",
                "upstream_model_name": "balanced-model",
                "timeout_seconds": 10,
                "retry": {
                    "max_attempts": 1,
                    "backoff_initial_ms": 1,
                    "backoff_max_ms": 5,
                },
                "limits": {"rpm": 100, "tpm": 100000, "concurrency": 5},
                "health": {"failure_threshold": 2, "cooldown_seconds": 1},
            },
            "model_d": {
                "provider": "openai_compatible",
                "provider_group": "openai",
                "base_url": "http://upstream-d/v1",
                "api_key": "k-d",
                "upstream_model_name": "strongest-model",
                "timeout_seconds": 10,
                "retry": {
                    "max_attempts": 1,
                    "backoff_initial_ms": 1,
                    "backoff_max_ms": 5,
                },
                "limits": {"rpm": 100, "tpm": 100000, "concurrency": 5},
                "health": {"failure_threshold": 2, "cooldown_seconds": 1},
            },
        },
        "telemetry": {
            "structured_logs": False,
            "log_level": "INFO",
            "expose_metrics": True,
            "debug_prompts": False,
        },
        "estimation": {
            "token_strategy": "best_effort",
            "chars_per_token_fallback": 4,
        },
        "streaming": {
            "enabled": True,
            "evaluator_streaming": False,
            "passthrough_streaming": True,
        },
    }


@pytest.fixture
def config_data() -> dict[str, Any]:
    return deepcopy(build_base_config())


@pytest.fixture
def app_config(config_data: dict[str, Any]) -> AppConfig:
    return AppConfig.model_validate(config_data)
