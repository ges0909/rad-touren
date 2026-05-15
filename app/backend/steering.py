"""Load steering files and assemble system prompt for the LLM."""

import logging
import re
from pathlib import Path

from tools import TOOL_DECLARATIONS

logger = logging.getLogger(__name__)

STEERING_DIR: Path = Path(__file__).parent.parent.parent / ".kiro" / "steering"

# Sections to strip from steering files before sending to Gemini.
# These reference tools/workflows that don't exist in the backend.
_SECTIONS_TO_STRIP: list[str] = [
    "Allowed MCP Servers",
    "MCP Tool Reference",
    "Map Rendering",
    "Trip Catalog Index",
    "Trip Lifecycle (Refreshing)",
    "File Structure",
]


def _sanitize_steering(content: str) -> str:
    """Remove sections that reference unavailable tools and rewrite workflow steps.

    The steering files are shared with Kiro (which has MCP tools), but the Gemini
    agent only has the tools in TOOL_REGISTRY. This function strips confusing
    sections and rewrites references to unavailable tools.
    """
    # Remove large sections by heading (## level) — everything from heading to next ## heading
    for section_title in _SECTIONS_TO_STRIP:
        pattern = rf"\n## {re.escape(section_title)}\s*\n.*?(?=\n## |\Z)"
        content = re.sub(pattern, "\n", content, flags=re.DOTALL)

    # Also remove ### subsections within remaining content
    subsections_to_strip = [
        "Routing & Geocoding",
        "Car Routing & GPX Export",
        "POIs",
        "Weather",
        "Travel Guides",
        "Hiking & Cycling Routes",
    ]
    for section_title in subsections_to_strip:
        pattern = rf"\n### {re.escape(section_title)}[^\n]*\n.*?(?=\n### |\n## |\Z)"
        content = re.sub(pattern, "\n", content, flags=re.DOTALL)

    # Rewrite workflow steps that reference remote_web_search
    # Catch patterns like: Search `remote_web_search` for "..."
    content = re.sub(
        r"[Ss]earch\s+`remote_web_search`\s+for\s+[^.]*\.",
        "Use your own knowledge.",
        content,
    )
    content = re.sub(
        r"[Ss]earch\s+for\s+[^.]*\s+via\s+`remote_web_search`[^.]*\.",
        "Use your own knowledge for this.",
        content,
    )
    content = re.sub(
        r"[Ss]earch\s+via\s+`remote_web_search`[^.]*\.",
        "Use your own knowledge.",
        content,
    )
    content = re.sub(
        r"[Ss]upplement\s+with\s+`remote_web_search`[^.]*\.",
        "",
        content,
    )
    content = re.sub(
        r"[Vv]erify\s+via\s+`remote_web_search`[^.]*:",
        "Note from your knowledge:",
        content,
    )
    content = re.sub(
        r"[Uu]se\s+`remote_web_search`[^.]*\.",
        "Use your own knowledge.",
        content,
    )
    # Catch any remaining backtick references
    content = content.replace("`remote_web_search`", "your own knowledge")
    content = content.replace("`mcp_wikivoyage_*`", "`search_destinations`/`get_article`")
    content = content.replace("`mcp_waymarkedtrails_*`", "`search_routes`")

    # Replace MCP tool references with actual tool names
    content = content.replace("`mcp_openrouteservice_geocode`", "`geocode`")
    content = content.replace("`mcp_openrouteservice_driving_time`", "`calculate_car_route`")
    content = content.replace("`driving_time`", "`calculate_car_route`")
    content = content.replace("`distance_matrix`", "`calculate_car_route`")

    # Remove any lines still containing mcp_ tool references (table rows, code blocks)
    lines = content.split("\n")
    lines = [line for line in lines if "mcp_" not in line]
    content = "\n".join(lines)

    # Clean up excessive blank lines
    content = re.sub(r"\n{4,}", "\n\n\n", content)

    return content


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


def build_system_prompt(
    tour_type: str = "road", language: str = "de", user_message: str = ""
) -> str:
    """Assemble system prompt from relevant steering files.

    Detects tour type from user_message and loads only the matching files
    to keep the prompt compact.

    Args:
        tour_type: Tour type hint (overridden by user_message detection).
        language: Output language code ("de" or "en").
        user_message: The user's input, used to detect tour type.

    Returns:
        Combined steering content as a single string.
    """
    # Base instructions for agent behavior (always English, output language controlled separately)
    lang_name = "German" if language == "de" else "English"

    # Build explicit tool list from declarations
    tool_names = [decl["name"] for decl in TOOL_DECLARATIONS]
    tool_list_str = ", ".join(f"`{name}`" for name in tool_names)

    base_prompt: str = f"""You are a travel planning assistant. You help plan cycling tours, hikes, and road trips.

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

## Available Tools — STRICT

You have access to EXACTLY these tools and NO others: {tool_list_str}

You do NOT have access to: `search`, `web_search`, `remote_web_search`, `driving_time`, `distance_matrix`, `isochrone`, or any `mcp_*` prefixed tools.
If the steering instructions below mention `remote_web_search` or MCP tools, IGNORE those steps and use your own knowledge instead.
NEVER call a tool that is not in the list above. If you need information that no tool can provide, use your training knowledge directly.

## Tool Mapping

When steering instructions reference these names, use the corresponding available tool:
- `mcp_openrouteservice_geocode` or `geocode` → use `geocode`
- `mcp_openrouteservice_driving_time` or `driving_time` → use `calculate_car_route` (provides distance + duration)
- `mcp_osrm_calculate_car_route` → use `calculate_car_route`
- `mcp_open_meteo_weather_forecast` → use `weather_forecast`
- `mcp_wikivoyage_search_destinations` → use `search_destinations`
- `mcp_wikivoyage_get_article` or `get_section` → use `get_article`
- `mcp_wikivoyage_search_nearby` → use `search_nearby`
- `mcp_waymarkedtrails_search_routes` → use `search_routes`
- `remote_web_search` → NOT available, use your own knowledge

## Template Selection

Detect the tour type from the user input and use the matching template:
- Cycling tour → "Bike Tour Output Template"
- Road trip → "Roadtrip Output Template"
- Hiking → Use a sensible Markdown structure (no dedicated template available)

Follow the chosen template structure strictly.
"""

    # Select files based on detected tour type
    detected = _detect_tour_type(user_message) if user_message else tour_type
    files: list[str] = ["user-preferences.md"]

    if detected == "bike":
        files += ["bike-planning.md", "bike-template.md"]
    elif detected == "road":
        files += ["road-planning.md", "road-template.md"]
    # "general" → only user-preferences, keep prompt small

    parts: list[str] = []
    loaded_count = 0
    for filename in files:
        path: Path = STEERING_DIR / filename
        if path.exists():
            content: str = path.read_text(encoding="utf-8")
            # Strip YAML front matter
            if content.startswith("---"):
                end: int = content.find("---", 3)
                if end != -1:
                    content = content[end + 3 :].strip()
            # Sanitize: remove references to unavailable tools
            content = _sanitize_steering(content)
            parts.append(content)
            loaded_count += 1
        else:
            logger.debug("Steering file not found: %s", filename)

    prompt = base_prompt + "\n\n---\n\n".join(parts)
    logger.info("System prompt built: %d files loaded, %d chars total", loaded_count, len(prompt))
    return prompt
