"""Simple i18n for user-facing error messages."""

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


def msg(key: str, lang: Lang, **kwargs: str | int) -> str:
    """Get a localized message by key, formatted with kwargs."""
    template = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("en", key))
    return template.format(**kwargs) if kwargs else template
