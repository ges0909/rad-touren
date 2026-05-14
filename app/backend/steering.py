"""Load steering files and assemble system prompt for the LLM."""

from pathlib import Path

STEERING_DIR = Path(__file__).parent.parent.parent / ".kiro" / "steering"


def build_system_prompt(tour_type: str = "road") -> str:
    """Assemble system prompt from all steering files.

    The agent receives all templates and selects the appropriate one
    based on the user's request.

    Returns:
        Combined steering content as a single string.
    """
    # Base instructions for agent behavior
    base_prompt = """Du bist ein Reiseplanungs-Assistent. Du hilfst bei der Planung von Radtouren, Wanderungen und Roadtrips.

## Wichtige Verhaltensregeln

- Zeige dem Nutzer NIEMALS interne Fehlermeldungen, Tool-Fehler oder Retry-Strategien.
- Wenn ein Tool fehlschlägt, versuche eine Alternative oder liefere das bestmögliche Ergebnis mit den verfügbaren Daten.
- Beschreibe NICHT deine internen Schritte ("Ich werde jetzt...", "Die Suche ist fehlgeschlagen..."). Liefere direkt das Ergebnis.
- Antworte immer in der Sprache des Nutzers.
- Strukturiere Ergebnisse übersichtlich mit Markdown.

## Template-Auswahl

Erkenne aus der Nutzereingabe den Tour-Typ und verwende das passende Template:
- Radtour/Fahrradtour → "Bike Tour Output Template"
- Roadtrip/Autoreise → "Roadtrip Output Template"
- Wanderung → Verwende eine sinnvolle Markdown-Struktur (kein dediziertes Template vorhanden)

Halte dich strikt an die Struktur des gewählten Templates.
"""

    # Load all steering files
    files = [
        "user-preferences.md",
        "bike-planning.md",
        "bike-template.md",
        "road-planning.md",
        "road-template.md",
    ]

    parts = []
    for filename in files:
        path = STEERING_DIR / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            # Strip YAML front matter
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            parts.append(content)

    return base_prompt + "\n\n---\n\n".join(parts)
