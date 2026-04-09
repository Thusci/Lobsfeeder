from __future__ import annotations


def build_evaluator_system_prompt(difficulty_levels: list[str]) -> str:
    levels = ", ".join(difficulty_levels)
    return (
        "You are a task difficulty classifier for an LLM routing gateway.\n"
        "Classify the user's request into exactly one difficulty tier.\n\n"
        f"Allowed tiers: {levels}\n\n"
        "Return JSON only:\n"
        "{\"difficulty\": \"<one allowed tier>\", \"reason\": \"<brief reason, max 20 words>\"}\n\n"
        "Rules:\n"
        "- Do not answer the user's task.\n"
        "- Do not include markdown.\n"
        "- Do not include code fences.\n"
        "- If uncertain, choose the nearest reasonable tier."
    )
