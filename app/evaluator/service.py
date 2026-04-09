from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.clients.registry import ClientRegistry
from app.core.errors import EvaluatorError
from app.core.settings import AppConfig
from app.evaluator.parser import ParsedDifficulty, parse_difficulty
from app.evaluator.prompt import build_evaluator_system_prompt


@dataclass
class EvaluatorResult:
    difficulty: str
    reason: str | None
    parse_mode: str


class EvaluatorService:
    def __init__(self, config: AppConfig, clients: ClientRegistry) -> None:
        self._config = config
        self._clients = clients

    def _shape_input(self, payload: dict[str, Any], max_chars: int = 4000) -> str:
        chunks: list[str] = []
        for msg in payload.get("messages", []):
            role = str(msg.get("role", "unknown"))
            content = msg.get("content", "")
            if isinstance(content, str):
                chunks.append(f"{role}: {content}")
            elif isinstance(content, list):
                chunks.append(f"{role}: {content}")

        merged = "\n".join(chunks)
        if len(merged) <= max_chars:
            return merged
        return merged[-max_chars:]

    async def classify(self, payload: dict[str, Any]) -> EvaluatorResult:
        routing = self._config.routing
        client = self._clients.get(routing.evaluator_model)

        prompt = build_evaluator_system_prompt(routing.difficulty_levels)
        user_text = self._shape_input(payload)

        evaluator_payload = {
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0,
            "max_tokens": 80,
            "stream": False,
        }

        try:
            response = await client.chat_completions(evaluator_payload)
            choices = response.response_json.get("choices")
            if not isinstance(choices, list) or not choices:
                raise EvaluatorError("Evaluator returned empty choices", retryable=True)

            first = choices[0]
            message = first.get("message") if isinstance(first, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str):
                raise EvaluatorError("Evaluator content missing", retryable=True)

            parsed: ParsedDifficulty = parse_difficulty(
                raw=content,
                allowed_tiers=routing.difficulty_levels,
                default_tier=routing.default_difficulty,
            )
            return EvaluatorResult(
                difficulty=parsed.difficulty,
                reason=parsed.reason,
                parse_mode=parsed.mode,
            )
        except EvaluatorError:
            raise
        except Exception as exc:
            raise EvaluatorError(f"Evaluator call failed: {exc}", retryable=True) from exc
