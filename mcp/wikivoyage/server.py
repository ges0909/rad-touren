"""MCP server wrapping the Wikivoyage API for travel guide content.

Uses lib.wikivoyage for all API logic. This file provides MCP tool declarations
and formats structured results into human-readable strings.
"""

import re
import sys
from pathlib import Path

from fastmcp import FastMCP

# Add lib/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.wikivoyage import (
    search_destinations as _search,
    get_article as _get_article,
    get_article_sections as _get_sections,
    search_nearby as _search_nearby,
)

mcp = FastMCP("Wikivoyage Travel Guides")


@mcp.tool()
async def search_destinations(query: str, lang: str = "de", results: int = 10) -> str:
    """Search for travel destinations on Wikivoyage.

    Args:
        query: Search query (destination name, region, or keyword).
               Examples: "Barcelona", "Spreewald", "Nordspanien"
        lang: Language edition — "de" (German, default) or "en" (English)
        results: Maximum number of results (1-20)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"

    result = await _search(query.strip(), lang, results)

    if "error" in result:
        return result["error"]

    destinations = result["destinations"]
    lines = [f"Gefunden: {len(destinations)} Ergebnis(se) auf {lang}.wikivoyage.org\n"]
    for d in destinations:
        size_kb = f"{d['size_bytes'] / 1024:.1f} KB" if d["size_bytes"] else ""
        lines.append(f"- **{d['title']}** ({size_kb})")
        if d["snippet"]:
            lines.append(f"  {d['snippet']}")
        lines.append(f"  → https://{lang}.wikivoyage.org/wiki/{d['title'].replace(' ', '_')}")

    return "\n".join(lines)


@mcp.tool()
async def get_article(title: str, lang: str = "de") -> str:
    """Get the full travel guide article for a destination.

    Returns the cleaned plain-text content of the Wikivoyage article.
    Use search_destinations first to find the exact article title.

    Args:
        title: Exact article title (e.g. "Barcelona", "Spreewald", "San Sebastián")
        lang: Language edition — "de" (German, default) or "en" (English)
    """
    if not title or len(title.strip()) < 2:
        return "Error: title must be at least 2 characters"

    result = await _get_article(title.strip(), lang)

    if "error" in result:
        return result["error"]

    content = result["content"]
    # Truncate very long articles
    max_chars = 12000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[... Artikel gekürzt. Nutze get_section() für einzelne Abschnitte.]"

    return f"# {result['title']}\nQuelle: https://{lang}.wikivoyage.org/wiki/{title.replace(' ', '_')}\n\n{content}"


@mcp.tool()
async def get_section(title: str, section: str, lang: str = "de") -> str:
    """Get a specific section from a Wikivoyage article.

    Useful for extracting targeted information like "Anreise" (getting there),
    "Sehenswürdigkeiten" (sights), "Küche" (food), "Aktivitäten" (activities).

    Args:
        title: Exact article title (e.g. "Barcelona", "Spreewald")
        section: Section name to extract. Common German sections:
                 Anreise, Mobilität, Sehenswürdigkeiten, Aktivitäten,
                 Einkaufen, Küche, Nachtleben, Unterkunft, Ausflüge
        lang: Language edition — "de" (German, default) or "en" (English)
    """
    if not title or not section:
        return "Error: title and section are required"

    # Get full article and extract section
    result = await _get_article(title.strip(), lang)

    if "error" in result:
        return result["error"]

    content = result["content"]

    # Find section by heading
    pattern = re.compile(rf"^## {re.escape(section)}\s*$", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return f"Abschnitt '{section}' nicht gefunden in '{title}'"

    start = match.start()
    # Find next section heading
    next_heading = re.search(r"^## ", content[match.end():], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(content)

    section_content = content[start:end].strip()
    return f"# {title} — {section}\n\n{section_content}"


@mcp.tool()
async def get_article_sections(title: str, lang: str = "de") -> str:
    """List all sections/headings of a Wikivoyage article.

    Useful to discover what information is available before fetching specific sections.

    Args:
        title: Exact article title (e.g. "Barcelona", "Spreewald")
        lang: Language edition — "de" (German, default) or "en" (English)
    """
    if not title or len(title.strip()) < 2:
        return "Error: title must be at least 2 characters"

    result = await _get_sections(title.strip(), lang)

    if "error" in result:
        return result["error"]

    sections = result["sections"]
    if not sections:
        return f"Keine Abschnitte gefunden für '{title}'"

    lines = [f"Abschnitte in '{title}':\n"]
    for s in sections:
        indent = "  " * (s["level"] - 2)
        lines.append(f"{indent}- {s['name']}")

    return "\n".join(lines)


@mcp.tool()
async def search_nearby(lat: float, lon: float, radius: int = 10000, lang: str = "de", results: int = 10) -> str:
    """Find Wikivoyage articles about places near given coordinates.

    Useful for discovering destinations close to a route or point of interest.

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        radius: Search radius in meters (max 10000)
        lang: Language edition — "de" (German, default) or "en" (English)
        results: Maximum number of results (1-50)
    """
    result = await _search_nearby(lat, lon, radius, lang, results)

    if "error" in result:
        return result["error"]

    places = result["places"]
    if not places:
        return f"Keine Wikivoyage-Artikel in der Nähe von {lat:.4f}, {lon:.4f}"

    lines = [f"Gefunden: {len(places)} Ort(e) in der Nähe:\n"]
    for p in places:
        dist_str = f"{p['distance_m']:.0f}m" if p.get("distance_m") else ""
        lines.append(f"- **{p['title']}** ({dist_str})")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
