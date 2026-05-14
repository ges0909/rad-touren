"""Load steering files and assemble system prompt for the LLM."""

from pathlib import Path

STEERING_DIR = Path(__file__).parent.parent.parent / ".kiro" / "steering"


def build_system_prompt(tour_type: str = "road") -> str:
    """Assemble system prompt from steering files based on tour type.

    Args:
        tour_type: One of "road", "bike", "hike".

    Returns:
        Combined steering content as a single string.
    """
    files = ["user-preferences.md"]

    if tour_type == "road":
        files += ["road-planning.md", "road-template.md"]
    elif tour_type == "bike":
        files += ["bike-planning.md", "bike-template.md"]
    elif tour_type == "hike":
        files += ["user-preferences.md"]  # No dedicated hike steering yet

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

    return "\n\n---\n\n".join(parts)
