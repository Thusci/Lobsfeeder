from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class ParsedDifficulty:
    difficulty: str
    reason: str | None
    mode: str


def _normalize(allowed: list[str]) -> dict[str, str]:
    return {name.strip().lower(): name for name in allowed}


def _extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None


def parse_difficulty(raw: str, allowed_tiers: list[str], default_tier: str) -> ParsedDifficulty:
    normalized = _normalize(allowed_tiers)
    fallback = normalized.get(default_tier.strip().lower(), default_tier)
    text = (raw or "").strip()

    if text:
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                difficulty = str(obj.get("difficulty", "")).strip().lower()
                reason = obj.get("reason")
                if difficulty in normalized:
                    return ParsedDifficulty(normalized[difficulty], str(reason) if reason else None, "strict_json")
        except json.JSONDecodeError:
            pass

    json_candidate = _extract_first_json_object(text)
    if json_candidate:
        try:
            obj = json.loads(json_candidate)
            if isinstance(obj, dict):
                difficulty = str(obj.get("difficulty", "")).strip().lower()
                reason = obj.get("reason")
                if difficulty in normalized:
                    return ParsedDifficulty(normalized[difficulty], str(reason) if reason else None, "balanced_json")
        except json.JSONDecodeError:
            pass

    regex = re.search(r'"difficulty"\s*:\s*"([^"]+)"', text, flags=re.IGNORECASE)
    if regex:
        maybe = regex.group(1).strip().lower()
        if maybe in normalized:
            return ParsedDifficulty(normalized[maybe], None, "regex_field")

    lowered = text.lower()
    for value_lower, canonical in normalized.items():
        if re.search(rf"\b{re.escape(value_lower)}\b", lowered):
            return ParsedDifficulty(canonical, None, "regex_tier")

    return ParsedDifficulty(fallback, None, "default")
