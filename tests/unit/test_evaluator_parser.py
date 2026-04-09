from app.evaluator.parser import parse_difficulty


def test_parse_strict_json() -> None:
    parsed = parse_difficulty('{"difficulty":"hard","reason":"complex"}', ["easy", "hard"], "easy")
    assert parsed.difficulty == "hard"
    assert parsed.mode == "strict_json"


def test_parse_json_embedded_text() -> None:
    parsed = parse_difficulty("Result: {\"difficulty\":\"easy\"}", ["easy", "hard"], "hard")
    assert parsed.difficulty == "easy"


def test_parse_regex_recovery() -> None:
    parsed = parse_difficulty("difficulty: HARD", ["easy", "hard"], "easy")
    assert parsed.difficulty == "hard"


def test_parse_default_fallback() -> None:
    parsed = parse_difficulty("n/a", ["easy", "hard"], "easy")
    assert parsed.difficulty == "easy"
    assert parsed.mode == "default"
