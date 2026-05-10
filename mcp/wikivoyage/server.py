"""MCP server wrapping the Wikivoyage MediaWiki API for travel information.

Provides tools to search for destinations, retrieve travel guides, and extract
structured sections (Anreise, Sehenswürdigkeiten, Küche, etc.) from Wikivoyage.
Supports both German (de) and English (en) Wikivoyage editions.
"""

import re

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Wikivoyage Travel Guide")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_LANGS = ("de", "en")
BASE_URL_TEMPLATE = "https://{lang}.wikivoyage.org/w/api.php"

# Common section names in German Wikivoyage articles
DE_SECTIONS = {
    "anreise": "Anreise",
    "mobilität": "Mobilität",
    "sehenswürdigkeiten": "Sehenswürdigkeiten",
    "aktivitäten": "Aktivitäten",
    "einkaufen": "Einkaufen",
    "küche": "Küche",
    "nachtleben": "Nachtleben",
    "unterkunft": "Unterkunft",
    "gesundheit": "Gesundheit",
    "praktische hinweise": "Praktische Hinweise",
    "ausflüge": "Ausflüge",
    "literatur": "Literatur",
    "weblinks": "Weblinks",
}


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


async def _get_json(lang: str, params: dict) -> dict | list | str:
    """Make GET request to Wikivoyage API and return JSON or error string."""
    if lang not in SUPPORTED_LANGS:
        return f"Error: unsupported language '{lang}'. Use one of: {SUPPORTED_LANGS}"

    url = BASE_URL_TEMPLATE.format(lang=lang)
    params["format"] = "json"
    params["formatversion"] = "2"

    headers = {
        "User-Agent": "WikivoyageMCP/1.0 (https://github.com/rad-touren; travel planning tool)",
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error {e.response.status_code}: {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_wikitext(text: str) -> str:
    """Remove common wikitext markup for readable plain text output."""
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove templates like {{...}} (simple, non-nested)
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    # Convert [[Link|Display]] to Display, [[Link]] to Link
    text = re.sub(r"\[\[[^|\]]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Convert external links [url text] to text
    text = re.sub(r"\[https?://[^\s\]]+ ([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\]]+\]", "", text)
    # Remove bold/italic markup
    text = re.sub(r"'{2,3}", "", text)
    # Remove <ref>...</ref>
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/?>", "", text)
    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_section(wikitext: str, section_name: str) -> str | None:
    """Extract a specific section from wikitext by heading name."""
    # Match == Section == or === Subsection ===
    pattern = rf"(^|\n)==\s*{re.escape(section_name)}\s*==\s*\n"
    match = re.search(pattern, wikitext, re.IGNORECASE)
    if not match:
        return None

    start = match.end()
    # Find the next section at same or higher level
    next_section = re.search(r"\n==\s*[^=]", wikitext[start:])
    if next_section:
        end = start + next_section.start()
    else:
        end = len(wikitext)

    return wikitext[start:end].strip()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


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
    if not (1 <= results <= 20):
        return "Error: results must be between 1 and 20"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query.strip(),
        "srlimit": results,
        "srnamespace": "0",
        "srprop": "snippet|titlesnippet|size",
    }

    data = await _get_json(lang, params)
    if isinstance(data, str):
        return data

    search_results = data.get("query", {}).get("search", [])
    if not search_results:
        return f"Keine Ergebnisse für '{query}' auf {lang}.wikivoyage.org"

    lines = [f"Gefunden: {len(search_results)} Ergebnis(se) auf {lang}.wikivoyage.org\n"]
    for item in search_results:
        title = item.get("title", "?")
        snippet = item.get("snippet", "")
        # Clean HTML from snippet
        snippet = re.sub(r"<[^>]+>", "", snippet).strip()
        size = item.get("size", 0)
        size_kb = f"{size / 1024:.1f} KB" if size else ""

        lines.append(f"- **{title}** ({size_kb})")
        if snippet:
            lines.append(f"  {snippet[:150]}")
        lines.append(f"  → https://{lang}.wikivoyage.org/wiki/{title.replace(' ', '_')}")

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

    params = {
        "action": "query",
        "titles": title.strip(),
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
    }

    data = await _get_json(lang, params)
    if isinstance(data, str):
        return data

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return f"Artikel '{title}' nicht gefunden auf {lang}.wikivoyage.org"

    page = pages[0]
    if page.get("missing"):
        return f"Artikel '{title}' existiert nicht auf {lang}.wikivoyage.org"

    revisions = page.get("revisions", [])
    if not revisions:
        return f"Kein Inhalt für '{title}' verfügbar"

    content = revisions[0].get("slots", {}).get("main", {}).get("content", "")
    if not content:
        return f"Leerer Artikel: '{title}'"

    cleaned = _clean_wikitext(content)

    # Truncate very long articles to stay within reasonable output
    max_chars = 12000
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[... Artikel gekürzt. Nutze get_section() für einzelne Abschnitte.]"

    header = (
        f"# {page.get('title', title)}\n"
        f"Quelle: https://{lang}.wikivoyage.org/wiki/{title.replace(' ', '_')}\n\n"
    )
    return header + cleaned


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
    if not title or len(title.strip()) < 2:
        return "Error: title must be at least 2 characters"
    if not section or len(section.strip()) < 2:
        return "Error: section name must be at least 2 characters"

    params = {
        "action": "query",
        "titles": title.strip(),
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
    }

    data = await _get_json(lang, params)
    if isinstance(data, str):
        return data

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return f"Artikel '{title}' nicht gefunden"

    page = pages[0]
    if page.get("missing"):
        return f"Artikel '{title}' existiert nicht auf {lang}.wikivoyage.org"

    revisions = page.get("revisions", [])
    if not revisions:
        return f"Kein Inhalt für '{title}' verfügbar"

    content = revisions[0].get("slots", {}).get("main", {}).get("content", "")
    if not content:
        return f"Leerer Artikel: '{title}'"

    section_text = _extract_section(content, section.strip())
    if not section_text:
        # Try case-insensitive lookup in known sections
        section_lower = section.strip().lower()
        if section_lower in DE_SECTIONS:
            section_text = _extract_section(content, DE_SECTIONS[section_lower])

    if not section_text:
        # List available sections as help
        available = re.findall(r"\n==\s*([^=]+?)\s*==", content)
        available_str = ", ".join(available[:15]) if available else "keine gefunden"
        return (
            f"Abschnitt '{section}' nicht gefunden in '{title}'.\n"
            f"Verfügbare Abschnitte: {available_str}"
        )

    cleaned = _clean_wikitext(section_text)
    header = f"## {section} — {page.get('title', title)}\n\n"
    return header + cleaned


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

    params = {
        "action": "parse",
        "page": title.strip(),
        "prop": "sections",
    }

    data = await _get_json(lang, params)
    if isinstance(data, str):
        return data

    if "error" in data:
        return f"Fehler: {data['error'].get('info', 'Unbekannter Fehler')}"

    sections = data.get("parse", {}).get("sections", [])
    if not sections:
        return f"Keine Abschnitte gefunden für '{title}'"

    page_title = data.get("parse", {}).get("title", title)
    lines = [f"Abschnitte in **{page_title}** ({lang}.wikivoyage.org):\n"]

    for sec in sections:
        level = int(sec.get("toclevel", 1))
        name = sec.get("line", "?")
        indent = "  " * (level - 1)
        lines.append(f"{indent}- {name}")

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
    if not (-90 <= lat <= 90):
        return "Error: latitude must be between -90 and 90"
    if not (-180 <= lon <= 180):
        return "Error: longitude must be between -180 and 180"
    if not (100 <= radius <= 10000):
        return "Error: radius must be between 100 and 10000 meters"
    if not (1 <= results <= 50):
        return "Error: results must be between 1 and 50"

    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": radius,
        "gslimit": results,
        "gsnamespace": "0",
    }

    data = await _get_json(lang, params)
    if isinstance(data, str):
        return data

    places = data.get("query", {}).get("geosearch", [])
    if not places:
        return f"Keine Wikivoyage-Artikel im Umkreis von {radius}m um {lat}, {lon}"

    lines = [f"Gefunden: {len(places)} Ort(e) im Umkreis von {radius}m:\n"]
    for place in places:
        title = place.get("title", "?")
        dist = place.get("dist", 0)
        plat = place.get("lat", "?")
        plon = place.get("lon", "?")

        dist_str = f"{dist:.0f}m" if dist < 1000 else f"{dist / 1000:.1f}km"
        lines.append(
            f"- **{title}** ({dist_str} entfernt)\n"
            f"  Koordinaten: {plat}, {plon}\n"
            f"  → https://{lang}.wikivoyage.org/wiki/{title.replace(' ', '_')}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
