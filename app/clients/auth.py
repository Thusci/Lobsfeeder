from __future__ import annotations

import json
from pathlib import Path

from app.core.errors import UpstreamAuthError
from app.core.settings import ModelConfig


def build_upstream_auth_headers(config: ModelConfig) -> dict[str, str]:
    if config.provider == "openai_compatible":
        api_key = (config.api_key or "").strip()
        if not api_key:
            raise UpstreamAuthError("Missing API key for openai_compatible provider")
        header_name = (config.api_key_header or "Authorization").strip()
        header_prefix = config.api_key_prefix or ""
        return {header_name: f"{header_prefix}{api_key}"}

    if config.provider == "openai-codex-oauth":
        token_path = Path((config.oauth_token_path or "~/.codex/auth.json")).expanduser()
        try:
            payload = json.loads(token_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise UpstreamAuthError(f"Codex OAuth token file not found: {token_path}") from exc
        except json.JSONDecodeError as exc:
            raise UpstreamAuthError(f"Codex OAuth token file is invalid JSON: {token_path}") from exc

        tokens = payload.get("tokens")
        if not isinstance(tokens, dict):
            raise UpstreamAuthError("Codex OAuth token file missing tokens object")

        access_token = tokens.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise UpstreamAuthError("Codex OAuth token file missing access_token")

        return {"Authorization": f"Bearer {access_token.strip()}"}

    raise UpstreamAuthError(f"Unsupported provider: {config.provider}")
