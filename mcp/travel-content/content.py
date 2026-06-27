"""Pure HTTP client logic for travel content search (blogs & videos).

No FastMCP dependency — importable independently for testing.
Uses Tavily API for web search and content extraction.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com"

# ---------------------------------------------------------------------------
# Trusted sources — quality newspapers, travel magazines, public broadcasters
# ---------------------------------------------------------------------------

TRUSTED_SOURCES: dict[str, list[str]] = {
    # German quality press
    "de_press": [
        "spiegel.de",
        "zeit.de",
        "sueddeutsche.de",
        "faz.net",
        "tagesspiegel.de",
        "welt.de",
    ],
    # Travel magazines (DE + international)
    "travel_magazines": [
        "geo.de",
        "merian.de",
        "nationalgeographic.de",
        "lonelyplanet.com",
        "roughguides.com",
        "cntraveler.com",
    ],
    # International quality press
    "international": [
        "theguardian.com",
        "bbc.com",
        "nytimes.com",
    ],
    # German public broadcasters (web articles and travel features)
    "oer": [
        "ndr.de",
        "br.de",
        "swr.de",
        "wdr.de",
        "ardmediathek.de",
    ],
    # Cycling: route databases and federation (not random blogs)
    "cycling": [
        "komoot.de",
        "outdooractive.com",
        "adfc.de",
        "radreise-wiki.de",
    ],
    # Regional official tourism + quality regional press
    "spain": ["spain.info", "elpais.com", "nationalgeographic.com.es"],
    "italy": ["italia.it", "enit.it", "nationalgeographic.it"],
    "france": ["france.fr", "lemonde.fr"],
    "scandinavia": ["visitnorway.de", "visitsweden.de", "visitfinland.com"],
    "finland": ["visitfinland.com", "yle.fi"],
}


def get_source_domains(region: str, activity: str) -> list[str]:
    """Return up to 5 trusted media domains relevant to region and activity.

    Cycling tours use route databases; all other activities use quality press
    and travel magazines.
    """
    if activity in ("cycling", "bikepacking"):
        base = ["komoot.de", "outdooractive.com", "adfc.de", "geo.de", "merian.de"]
    else:
        base = ["geo.de", "merian.de", "spiegel.de", "theguardian.com", "nationalgeographic.de"]

    # Add up to 2 region-specific sources
    regional: list[str] = []
    region_lower = region.lower()
    for key, sources in TRUSTED_SOURCES.items():
        if key in region_lower or region_lower in key:
            regional.extend(sources[:2])

    # Regional sources take priority, fill rest with base
    combined = regional + base
    seen: set[str] = set()
    result: list[str] = []
    for d in combined:
        if d not in seen:
            seen.add(d)
            result.append(d)

    return result[:5]  # Tavily include_domains limit


# ---------------------------------------------------------------------------
# Tavily search helper
# ---------------------------------------------------------------------------


async def tavily_search(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = None,
    search_depth: str = "advanced",
    include_raw_content: bool = True,
) -> dict:
    """Search via Tavily with optional domain filtering.

    Returns raw API response as dict, or {"error": "..."} on failure.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}

    body: dict = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": include_raw_content,
    }
    if include_domains:
        body["include_domains"] = include_domains[:5]  # Tavily limit

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{TAVILY_BASE_URL}/search", json=body)
    except httpx.TimeoutException:
        return {"error": "Request timed out"}

    if response.status_code != 200:
        return {"error": f"Tavily API returned {response.status_code}"}

    return response.json()


async def tavily_extract(url: str) -> dict:
    """Extract content from a URL via Tavily.

    Returns raw API response as dict, or {"error": "..."} on failure.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}

    if not url or not url.startswith(("http://", "https://")):
        return {"error": "url must start with http:// or https://"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TAVILY_BASE_URL}/extract",
                json={
                    "api_key": TAVILY_API_KEY,
                    "urls": [url],
                },
            )
    except httpx.TimeoutException:
        return {"error": "Request timed out"}

    if response.status_code != 200:
        return {"error": f"Tavily API returned {response.status_code}"}

    return response.json()


# ---------------------------------------------------------------------------
# YouTube transcript helper
# ---------------------------------------------------------------------------


async def get_youtube_transcript(video_id: str) -> str | None:
    """Attempt to fetch YouTube transcript via a public transcript service."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://youtubetranscript.com/?server_vid2={video_id}",
                headers={"User-Agent": "travel-content-mcp/1.0"},
            )
            if resp.status_code == 200 and resp.text.strip():
                try:
                    root = ET.fromstring(resp.text)
                    texts = [elem.text or "" for elem in root.findall(".//text")]
                    return " ".join(texts)[:5000]
                except ET.ParseError:
                    return None
    except Exception:
        return None
    return None
