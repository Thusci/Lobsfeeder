from __future__ import annotations

from typing import Any


class TokenEstimator:
    def __init__(self, chars_per_token: int = 4) -> None:
        self.chars_per_token = max(chars_per_token, 1)

    def estimate_request_tokens(self, payload: dict[str, Any]) -> int:
        text = []
        for msg in payload.get("messages", []):
            content = msg.get("content")
            if isinstance(content, str):
                text.append(content)
            elif isinstance(content, list):
                text.extend(str(item) for item in content)
        if payload.get("tools"):
            text.append(str(payload.get("tools")))
        if payload.get("response_format"):
            text.append(str(payload.get("response_format")))

        total_chars = len("\n".join(text))
        return max(total_chars // self.chars_per_token, 1)

    def resolve_actual_tokens(self, response_json: dict[str, Any] | None, estimated: int) -> int:
        if not response_json:
            return estimated

        usage = response_json.get("usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int) and total > 0:
                return total

            prompt = usage.get("prompt_tokens")
            completion = usage.get("completion_tokens")
            if isinstance(prompt, int) and isinstance(completion, int):
                return max(prompt + completion, 1)

        return estimated
