"""
Language detection utility for multi-language scorer support.

Uses `langdetect` (a Python port of Google's language-detect library).
Falls back to "en" if detection fails or the library is unavailable.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Languages that use the Latin script and follow standard capitalisation rules
_LATIN_SCRIPT_LANGS = {
    "en", "de", "fr", "es", "it", "pt", "nl", "sv", "da", "no", "fi",
    "pl", "cs", "sk", "ro", "hr", "sl", "lt", "lv", "et", "hu", "tr",
    "id", "ms", "vi", "af", "sw", "tl",
}

# Agglutinative languages where word-level TTR is naturally lower
_AGGLUTINATIVE_LANGS = {"tr", "fi", "hu", "et", "lv", "lt", "ka", "az", "uz"}


def detect_language(text: str) -> str:
    """Detect the language of *text*. Returns an ISO 639-1 code (e.g. "en").

    Falls back to "en" on any detection error.
    """
    try:
        from langdetect import detect  # type: ignore
        return detect(text)
    except Exception as exc:
        logger.debug("Language detection failed (%s); defaulting to 'en'.", exc)
        return "en"


def is_latin_script(lang: str) -> bool:
    return lang in _LATIN_SCRIPT_LANGS


def is_agglutinative(lang: str) -> bool:
    return lang in _AGGLUTINATIVE_LANGS
