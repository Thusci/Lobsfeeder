from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


ENV_VAR_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


class RetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=1, ge=1, le=5)
    backoff_initial_ms: int = Field(default=200, ge=0, le=30000)
    backoff_max_ms: int = Field(default=1500, ge=0, le=60000)


class LimitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rpm: int = Field(gt=0)
    tpm: int = Field(gt=0)
    concurrency: int = Field(gt=0)


class HealthConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    failure_threshold: int = Field(default=5, ge=1)
    cooldown_seconds: int = Field(default=30, ge=1)


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["openai_compatible"]
    base_url: str
    api_key: str
    upstream_model_name: str
    timeout_seconds: int = Field(default=60, ge=1, le=600)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    limits: LimitConfig
    health: HealthConfig = Field(default_factory=HealthConfig)


class FallbackPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Literal["fallback", "queue", "reject"] = "fallback"
    ordered_candidates: dict[str, list[str]] = Field(default_factory=dict)
    max_fallback_hops: int = Field(default=2, ge=0, le=20)
    on_evaluator_error_use_default_difficulty: bool = True
    queue_wait_ms: int = Field(default=250, ge=0, le=60000)
    queue_poll_interval_ms: int = Field(default=25, ge=1, le=5000)


class GlobalLimitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_rpm: int | None = Field(default=None, gt=0)
    total_concurrency: int | None = Field(default=None, gt=0)


class RoutingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    evaluator_model: str
    default_difficulty: str
    allow_request_override: bool = True
    override_field_mode: str = "alias"
    difficulty_levels: list[str]
    difficulty_to_model: dict[str, str]
    fallback_policy: FallbackPolicyConfig = Field(default_factory=FallbackPolicyConfig)
    strict_mode: bool = False
    allow_evaluator_as_candidate: bool = False

    @model_validator(mode="after")
    def validate_difficulties(self) -> "RoutingConfig":
        normalized = [x.strip().lower() for x in self.difficulty_levels]
        if len(normalized) != len(set(normalized)):
            raise ValueError("difficulty_levels contains duplicates")

        if self.default_difficulty.strip().lower() not in set(normalized):
            raise ValueError("default_difficulty must exist in difficulty_levels")

        missing_map_keys = [level for level in self.difficulty_levels if level not in self.difficulty_to_model]
        if missing_map_keys:
            raise ValueError(f"difficulty_to_model missing keys: {missing_map_keys}")
        return self


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "0.0.0.0"
    port: int = Field(default=8080, ge=1, le=65535)
    request_timeout_seconds: int = Field(default=120, ge=1, le=3600)
    max_request_body_mb: int = Field(default=8, ge=1, le=128)
    max_messages: int = Field(default=256, ge=1, le=10000)
    max_tools: int = Field(default=128, ge=0, le=4096)
    max_stop_sequences: int = Field(default=32, ge=0, le=512)
    max_message_chars: int = Field(default=200000, ge=1, le=10000000)
    max_tool_definition_chars: int = Field(default=400000, ge=1, le=10000000)
    global_limits: GlobalLimitConfig = Field(default_factory=GlobalLimitConfig)
    router_api_keys: list[str] = Field(default_factory=list)


class TelemetryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    structured_logs: bool = True
    log_level: str = "INFO"
    expose_metrics: bool = True
    debug_prompts: bool = False


class EstimationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token_strategy: Literal["best_effort"] = "best_effort"
    chars_per_token_fallback: int = Field(default=4, ge=1, le=20)


class StreamingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    evaluator_streaming: bool = False
    passthrough_streaming: bool = True


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: ServerConfig
    routing: RoutingConfig
    models: dict[str, ModelConfig]
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    estimation: EstimationConfig = Field(default_factory=EstimationConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)

    @model_validator(mode="after")
    def validate_refs(self) -> "AppConfig":
        if self.routing.evaluator_model not in self.models:
            raise ValueError("routing.evaluator_model is not defined in models")

        undefined = [
            model_key
            for model_key in self.routing.difficulty_to_model.values()
            if model_key not in self.models
        ]
        if undefined:
            raise ValueError(f"difficulty_to_model references undefined models: {undefined}")

        fallback_undefined: list[str] = []
        for _, candidates in self.routing.fallback_policy.ordered_candidates.items():
            for model_key in candidates:
                if model_key not in self.models:
                    fallback_undefined.append(model_key)
        if fallback_undefined:
            raise ValueError(f"fallback_policy references undefined models: {sorted(set(fallback_undefined))}")

        return self


def _interpolate_env(raw: str) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Missing environment variable: {key}")
        return value

    return ENV_VAR_RE.sub(replace, raw)


def load_config(path: str | None = None) -> AppConfig:
    config_path = Path(path or os.getenv("ROUTER_CONFIG", "config/config.yaml"))
    if not config_path.exists():
        alt = Path("config/config.example.yaml")
        if alt.exists():
            config_path = alt
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = config_path.read_text(encoding="utf-8")
    rendered = _interpolate_env(raw)
    data: Any = yaml.safe_load(rendered)
    if not isinstance(data, dict):
        raise ValueError("Config root must be a mapping")

    return AppConfig.model_validate(data)
