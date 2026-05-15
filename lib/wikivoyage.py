"""Wikivoyage API client — travel guide search and article retrieval."""

import re
from typing import Any

import httpx

BASE_URL_TEMPLATE = "https://{lang}.wikivoyage.org/w/api.php"
SUPPORTED_LANGS = ("de", "en")
TIMEOUT = 30
HEADERS = {"User-Agent": "TripPlanner/1.0 (travel planning tool)"}


async def _get(lang: str, params: dict[str, Any]) -> dict[str, Any]:
    """Make GET request to Wikivoyage MediaWiki API."""
    url = BASE_URL_TEMPLATE.format(lang=lang)
    params["format"] = "json"
    params["formatversion"] = "2"

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def _clean_wikitext(text: str) -> str:
    """Remove wiki markup, templates, and HTML from wikitext."""
    # Remove templates {{...}}
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    # Remove [[File:...]] and [[Image:...]]
    text = re.sub(r"\[\[(File|Image|Datei|Bild):[^\]]*\]\]", "", text)
    # Convert [[link|text]] to text, [[link]] to link
    text = re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    # Remove external links [url text] → text
    text = re.sub(r"\[https?://[^\s\]]+ ([^\]]*)\]", r"\1", text)
    text = re.sub(r"\[https?://[^\]]*\]", "", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Convert headers
    text = re.sub(r"^={2,}\s*(.+?)\s*={2,}$", r"## \1", text, flags=re.MULTILINE)
    # Remove bold/italic markup
    text = re.sub(r"'{2,3}", "", text)
    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def search_destinations(
    query: str, lang: str = "de", results: int = 10
) -> dict[str, Any]:
    """Search for travel destinations.

    Args:
        query: Destination name, region, or keyword.
        lang: Language edition ("de" or "en").
        results: Max results (1-20).
    """
    if lang not in SUPPORTED_LANGS:
        return {"error": f"Unsupported language: {lang}"}

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query.strip(),
        "srlimit": results,
        "srnamespace": "0",
        "srprop": "snippet|titlesnippet|size",
    }

    data = await _get(lang, params)
    search_results = data.get("query", {}).get("search", [])

    if not search_results:
        return {"error": f"No results for '{query}'"}

    destinations: list[dict[str, Any]] = []
    for item in search_results:
        snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")).strip()
        destinations.append({
            "title": item.get("title", "?"),
            "snippet": snippet[:150],
            "size_bytes": item.get("size", 0),
        })

    return {"destinations": destinations, "lang": lang}


async def get_article(title: str, lang: str = "de") -> dict[str, Any]:
    """Get full travel guide article content.

    Args:
        title: Exact article title.
        lang: Language edition.
    """
    if lang not in SUPPORTED_LANGS:
        return {"error": f"Unsupported language: {lang}"}

    params = {
        "action": "query",
        "titles": title.strip(),
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
    }

    data = await _get(lang, params)
    pages = data.get("query", {}).get("pages", [])

    if not pages or pages[0].get("missing"):
        return {"error": f"Article '{title}' not found"}

    page = pages[0]
    revisions = page.get("revisions", [])
    if not revisions:
        return {"error": f"No content for '{title}'"}

    content = revisions[0].get("slots", {}).get("main", {}).get("content", "")
    cleaned = _clean_wikitext(content)

    return {
        "title": page.get("title", title),
        "content": cleaned,
        "lang": lang,
    }


async def get_article_sections(title: str, lang: str = "de") -> dict[str, Any]:
    """Get list of sections/headings in an article.

    Args:
        title: Exact article title.
        lang: Language edition.
    """
    if lang not in SUPPORTED_LANGS:
        return {"error": f"Unsupported language: {lang}"}

    params = {
        "action": "parse",
        "page": title.strip(),
        "prop": "sections",
    }

    data = await _get(lang, params)
    sections_data = data.get("parse", {}).get("sections", [])

    sections: list[dict[str, Any]] = []
    for s in sections_data:
        sections.append({
            "name": s.get("line", "?"),
            "level": int(s.get("level", 2)),
            "index": s.get("index", ""),
        })

    return {"title": title, "sections": sections, "lang": lang}


async def search_nearby(
    lat: float, lon: float, radius: int = 10000, lang: str = "de", results: int = 10
) -> dict[str, Any]:
    """Find articles about places near coordinates.

    Args:
        lat: Latitude.
        lon: Longitude.
        radius: Search radius in meters (max 10000).
        lang: Language edition.
        results: Max results (1-50).
    """
    if lang not in SUPPORTED_LANGS:
        return {"error": f"Unsupported language: {lang}"}

    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": min(radius, 10000),
        "gslimit": results,
        "gsnamespace": "0",
    }

    data = await _get(lang, params)
    geo_results = data.get("query", {}).get("geosearch", [])

    places: list[dict[str, Any]] = []
    for r in geo_results:
        places.append({
            "title": r.get("title", "?"),
            "lat": r.get("lat"),
            "lon": r.get("lon"),
            "distance_m": r.get("dist"),
        })

    return {"places": places, "lang": lang}
