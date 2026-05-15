"""Simple i18n for user-facing error messages."""

import re
from typing import Literal

type Lang = Literal["de", "en"]

MESSAGES: dict[str, dict[Lang, str]] = {
    "quota_exhausted": {
        "de": "API-Quota erschöpft. Bitte warte einige Minuten oder prüfe dein Gemini-Kontingent.",
        "en": "API quota exhausted. Please wait a few minutes or check your Gemini quota.",
    },
    "api_error": {
        "de": "Gemini API-Fehler ({code}): {detail}",
        "en": "Gemini API error ({code}): {detail}",
    },
    "server_unavailable": {
        "de": "Gemini-Server nicht erreichbar ({code}). Bitte später erneut versuchen.",
        "en": "Gemini server unavailable ({code}). Please try again later.",
    },
    "unexpected_error": {
        "de": "Unerwarteter Fehler: {detail}",
        "en": "Unexpected error: {detail}",
    },
    "max_iterations": {
        "de": "Maximale Iterationen erreicht. Bitte versuche eine kürzere Anfrage.",
        "en": "Maximum iterations reached. Please try a shorter request.",
    },
    "no_api_key": {
        "de": "GEMINI_API_KEY ist nicht konfiguriert.",
        "en": "GEMINI_API_KEY is not configured.",
    },
    "internal_error": {
        "de": "Interner Fehler: {detail}",
        "en": "Internal error: {detail}",
    },
}


def detect_language(text: str) -> Lang:
    """Detect language from user input using simple heuristics.

    Returns 'de' for German, 'en' for English (default).
    """
    # Common German words/patterns
    german_indicators = re.compile(
        r"\b(und|oder|für|mit|eine?[mnrs]?|ist|das|die|der|nicht|"
        r"ich|wir|bitte|plane|radtour|wanderung|roadtrip|tage?|"
        r"woche[n]?|durch|nach|von|über|küste|stadt|region)\b",
        re.IGNORECASE,
    )
    matches = german_indicators.findall(text)
    # If 2+ German words found, assume German
    if len(matches) >= 2:
        return "de"
    return "en"


def msg(key: str, lang: Lang, **kwargs: str | int) -> str:
    """Get a localized message by key, formatted with kwargs."""
    template = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("en", key))
    return template.format(**kwargs) if kwargs else template
