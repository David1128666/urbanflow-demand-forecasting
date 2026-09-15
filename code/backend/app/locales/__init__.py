"""Small dependency-free localization helper for the API layer."""

from __future__ import annotations

from typing import Any

from app.config import APP_LANGUAGE
from app.locales import en, zh_CN


SUPPORTED_LANGUAGES = {
    "en": en.MESSAGES,
    "zh-CN": zh_CN.MESSAGES,
}
DEFAULT_LANGUAGE = "en"


def current_language() -> str:
    return (
        APP_LANGUAGE
        if APP_LANGUAGE in SUPPORTED_LANGUAGES
        else DEFAULT_LANGUAGE
    )


def translate(key: str, **values: Any) -> str:
    language = current_language()
    template = SUPPORTED_LANGUAGES[language].get(
        key,
        SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE].get(key, key),
    )
    return template.format(**values) if values else template
