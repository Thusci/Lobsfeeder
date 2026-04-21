from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI_JS = ROOT / "app" / "ui" / "app.js"
UI_HTML = ROOT / "app" / "ui" / "index.html"


def _extract_translation_keys() -> dict[str, set[str]]:
    keys: dict[str, set[str]] = {"en": set(), "zh": set()}
    current_lang: str | None = None

    for line in UI_JS.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "en: {":
            current_lang = "en"
            continue
        if stripped == "zh: {":
            current_lang = "zh"
            continue
        if current_lang and stripped == "},":
            current_lang = None
            continue

        if current_lang:
            match = re.match(r'^"([^"]+)":', stripped)
            if match:
                keys[current_lang].add(match.group(1))

    return keys


def _extract_html_i18n_keys() -> set[str]:
    html = UI_HTML.read_text(encoding="utf-8")
    return {
        match.group(1)
        for match in re.finditer(
            r'data-i18n(?:-placeholder|-aria-label)?="([^"]+)"',
            html,
        )
    }


def test_ui_translation_keysets_match_between_languages() -> None:
    keys = _extract_translation_keys()
    assert keys["en"] == keys["zh"]


def test_ui_template_keys_exist_in_translation_dictionary() -> None:
    keys = _extract_translation_keys()
    html_keys = _extract_html_i18n_keys()

    assert html_keys <= keys["en"]
    assert html_keys <= keys["zh"]
