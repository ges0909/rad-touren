"""Simple i18n for user-facing error messages and status labels."""

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
    # Tool group status messages
    "status_routing": {
        "de": "🗺️ Berechne Route …",
        "en": "🗺️ Calculating route …",
    },
    "status_location": {
        "de": "📍 Suche Orte …",
        "en": "📍 Searching locations …",
    },
    "status_weather": {
        "de": "🌤️ Prüfe Wetter …",
        "en": "🌤️ Checking weather …",
    },
    "status_transit": {
        "de": "🚆 Suche Nahverkehrsverbindungen …",
        "en": "🚆 Searching regional connections …",
    },
    "status_pois": {
        "de": "📌 Suche Sehenswürdigkeiten …",
        "en": "📌 Searching points of interest …",
    },
    "status_trails": {
        "de": "🥾 Suche Wander-/Radrouten …",
        "en": "🥾 Searching hiking/cycling trails …",
    },
    "status_travel_info": {
        "de": "📖 Suche Reiseinformationen …",
        "en": "📖 Searching travel information …",
    },
    "status_web_search": {
        "de": "🔍 Suche im Web …",
        "en": "🔍 Searching the web …",
    },
    "status_rendering": {
        "de": "🖼️ Erstelle Karte …",
        "en": "🖼️ Rendering map …",
    },
    "status_generic": {
        "de": "⚙️ Verarbeite …",
        "en": "⚙️ Processing …",
    },
}


def msg(key: str, lang: Lang, **kwargs: str | int) -> str:
    """Get a localized message by key, formatted with kwargs."""
    template = MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("en", key))
    return template.format(**kwargs) if kwargs else template
