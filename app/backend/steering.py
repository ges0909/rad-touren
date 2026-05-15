"""Load steering files and assemble system prompt for the LLM."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STEERING_DIR: Path = Path(__file__).parent.parent.parent / ".kiro" / "steering"


def _detect_tour_type(message: str) -> str:
    """Detect tour type from user message. Returns 'bike', 'road', or 'general'."""
    msg = message.lower()
    bike_words = ("radtour", "fahrrad", "bike", "cycling", "radweg", "radfahren", "e-bike")
    road_words = ("roadtrip", "road trip", "autoreise", "mietwagen", "rental car", "driving")

    if any(w in msg for w in bike_words):
        return "bike"
    if any(w in msg for w in road_words):
        return "road"
    return "general"


def _select_files(user_message: str) -> list[str]:
    """Select steering files based on detected tour type."""
    detected = _detect_tour_type(user_message) if user_message else "general"
    files: list[str] = ["user-preferences.md"]

    if detected == "bike":
        files += ["bike-planning.md", "bike-template.md"]
    elif detected == "road":
        files += ["road-planning.md", "road-template.md"]
    # "general" → only user-preferences, keep prompt small

    return files


def build_system_prompt(
    tool_names: list[str],
    language: str = "de",
    user_message: str = "",
) -> str:
    """Assemble system prompt. Tool names come from MCP manager.

    Args:
        tool_names: List of available tool names from MCPManager.
        language: Output language code ("de" or "en").
        user_message: The user's input, used to detect tour type.

    Returns:
        Combined steering content as a single string.
    """
    lang_name = "German" if language == "de" else "English"
    tool_list_str = ", ".join(f"`{name}`" for name in tool_names)

    base_prompt = f"""You are a travel planning assistant. You help plan cycling tours, hikes, and road trips.

## Critical Behavior Rules

- NEVER apologize for tool failures or mention technical problems to the user.
- NEVER say "I cannot plan this" or "please try again later". Always deliver something useful.
- If a tool returns an error, silently try a different approach or use your own knowledge to provide the best answer.
- NEVER describe your internal steps ("I will now...", "The search failed..."). Deliver the result directly.
- If geocoding fails, use well-known coordinates from your training data.
- If route search fails, suggest a route based on your knowledge of the region.
- Structure results clearly with Markdown.
- Respond ONLY in {lang_name}.
- To display a route on the map, call `calculate_car_route` or `calculate_bike_route` with waypoint coordinates. Without this call, no map will be shown.

## Available Tools
{tool_list_str}

## Template Selection

Detect the tour type from the user input and use the matching template:
- Cycling tour → "Bike Tour Output Template"
- Road trip → "Roadtrip Output Template"
- Hiking → Use a sensible Markdown structure (no dedicated template available)

Follow the chosen template structure strictly.
"""

    # Load steering files (no sanitization needed)
    parts: list[str] = [base_prompt]
    loaded_count = 0
    for filename in _select_files(user_message):
        path: Path = STEERING_DIR / filename
        if path.exists():
            content: str = path.read_text(encoding="utf-8")
            # Strip YAML front matter
            if content.startswith("---"):
                end: int = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            parts.append(content)
            loaded_count += 1
        else:
            logger.debug("Steering file not found: %s", filename)

    prompt = "\n\n---\n\n".join(parts)
    logger.info("System prompt built: %d files loaded, %d chars total", loaded_count, len(prompt))
    return prompt
