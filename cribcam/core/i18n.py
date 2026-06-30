"""Minimal i18n — load locale JSON, fall back to English."""

import json
import os

_strings: dict = {}
_locale: str = "en"


def load(language: str = "en") -> None:
    global _strings, _locale
    _locale = language
    base = os.path.join(os.path.dirname(__file__), "..", "i18n")
    path = os.path.join(base, f"{language}.json")
    fallback = os.path.join(base, "en.json")
    try:
        with open(path) as f:
            _strings = json.load(f)
    except Exception:
        with open(fallback) as f:
            _strings = json.load(f)


def t(key: str, **kwargs) -> str:
    text = _strings.get(key, key)
    return text.format(**kwargs) if kwargs else text
