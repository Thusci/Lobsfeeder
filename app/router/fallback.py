from __future__ import annotations

from app.core.settings import AppConfig


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def build_candidates(
    config: AppConfig,
    difficulty: str,
    override_model: str | None = None,
) -> list[str]:
    routing = config.routing
    candidates: list[str] = []

    if override_model:
        candidates.append(override_model)
        if not routing.strict_mode:
            default_pool = routing.fallback_policy.ordered_candidates.get(difficulty, [])
            candidates.extend(default_pool)
    else:
        primary = routing.difficulty_to_model[difficulty]
        candidates.append(primary)
        candidates.extend(routing.fallback_policy.ordered_candidates.get(difficulty, []))

    deduped = _dedupe(candidates)
    if not routing.allow_evaluator_as_candidate:
        deduped = [x for x in deduped if x != routing.evaluator_model]

    max_attempts = routing.fallback_policy.max_fallback_hops + 1
    return deduped[:max_attempts]
