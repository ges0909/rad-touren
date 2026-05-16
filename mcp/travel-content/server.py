"""MCP server for extracting structured travel recommendations from blogs and videos.

Searches curated travel blog sources and YouTube transcripts, then extracts
actionable route planning data: stops, highlights, warnings, restaurant tips.

Requires TAVILY_API_KEY environment variable for web search.
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com"

mcp = FastMCP("Travel Content")

# ---------------------------------------------------------------------------
# Curated blog sources by region/topic
# ---------------------------------------------------------------------------

BLOG_SOURCES: dict[str, list[str]] = {
    "cycling_de": [
        "radtouren.de",
        "bikepacking.com",
        "komoot.de",
        "outdooractive.com",
        "radreise-wiki.de",
        "velociped.de",
    ],
    "cycling_eu": [
        "bikepacking.com",
        "cyclingeurope.org",
        "warmshowers.org",
        "eurovelo.com",
    ],
    "roadtrip_eu": [
        "roadtrippers.com",
        "travelontoast.de",
        "bravebird.de",
        "off-the-path.com",
        "reisedepeschen.de",
        "journeyera.com",
    ],
    "spain": [
        "spanien-reisemagazin.de",
        "spain.info",
        "loveandroad.com",
        "saltinourhair.com",
    ],
    "italy": [
        "italien.de",
        "zainoo.com",
        "reise-nach-italien.de",
        "italymagazine.com",
    ],
    "france": [
        "frankreich-webazine.de",
        "france.fr",
        "thegoodlifefrance.com",
    ],
    "scandinavia": [
        "visitnorway.de",
        "visitsweden.de",
        "visitfinland.com",
        "nordlandblog.de",
    ],
}


def _get_source_domains(region: str, activity: str) -> list[str]:
    """Get relevant blog domains for a region/activity combination."""
    domains: list[str] = []

    # Activity-specific sources
    if activity in ("cycling", "bikepacking"):
        domains.extend(BLOG_SOURCES.get("cycling_de", []))
        domains.extend(BLOG_SOURCES.get("cycling_eu", []))
    elif activity in ("roadtrip", "driving"):
        domains.extend(BLOG_SOURCES.get("roadtrip_eu", []))

    # Region-specific sources
    region_lower = region.lower()
    for key, sources in BLOG_SOURCES.items():
        if key in region_lower or region_lower in key:
            domains.extend(sources)

    return list(set(domains))


# ---------------------------------------------------------------------------
# Tavily search helper
# ---------------------------------------------------------------------------


async def _tavily_search(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = None,
    search_depth: str = "advanced",
) -> dict:
    """Search via Tavily with optional domain filtering."""
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}

    body: dict = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": True,
    }
    if include_domains:
        body["include_domains"] = include_domains[:5]  # Tavily limit

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{TAVILY_BASE_URL}/search", json=body)

    if response.status_code != 200:
        return {"error": f"Tavily API returned {response.status_code}"}

    return response.json()


# ---------------------------------------------------------------------------
# YouTube transcript helper
# ---------------------------------------------------------------------------

YOUTUBE_TRANSCRIPT_URL = "https://www.youtube.com/watch?v={video_id}"


async def _get_youtube_transcript(video_id: str) -> str | None:
    """Attempt to fetch YouTube transcript via a public transcript service."""
    # Use a lightweight transcript extraction approach
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try the youtubetranscript.com API (no key needed)
            resp = await client.get(
                f"https://youtubetranscript.com/?server_vid2={video_id}",
                headers={"User-Agent": "travel-content-mcp/1.0"},
            )
            if resp.status_code == 200 and resp.text.strip():
                # Parse XML transcript
                import xml.etree.ElementTree as ET

                try:
                    root = ET.fromstring(resp.text)
                    texts = [elem.text or "" for elem in root.findall(".//text")]
                    return " ".join(texts)[:5000]  # Cap at 5000 chars
                except ET.ParseError:
                    return None
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_travel_blogs(
    query: str,
    region: str = "",
    activity: str = "roadtrip",
    max_results: int = 5,
) -> str:
    """Search travel blogs for route recommendations and local tips.

    Searches curated travel blog sources for practical information:
    route suggestions, restaurant tips, accommodation, warnings, hidden gems.

    Args:
        query: Search query (e.g. "Nordspanien Küste Roadtrip Geheimtipps",
               "Brandenburg Radtour Seen", "Sardinien beste Strände")
        region: Region to focus on (e.g. "spain", "italy", "brandenburg").
                Helps select relevant blog sources.
        activity: Type of travel — "roadtrip", "cycling", "bikepacking", "hiking"
        max_results: Number of blog posts to return (1-10, default 5)
    """
    if not query or len(query.strip()) < 3:
        return "Error: query must be at least 3 characters"

    # Build domain-filtered search
    domains = _get_source_domains(region, activity)
    search_query = f"{query} {activity} Erfahrungsbericht Tipps"

    data = await _tavily_search(
        query=search_query[:400],
        max_results=min(max_results, 10),
        include_domains=domains if domains else None,
        search_depth="advanced",
    )

    if "error" in data:
        return data["error"]

    lines: list[str] = []

    # AI summary
    answer = data.get("answer")
    if answer:
        lines.append(f"**Zusammenfassung:** {answer}\n")

    # Individual results
    results = data.get("results", [])
    if not results:
        return f"Keine Reiseblog-Ergebnisse für: {query}"

    lines.append(f"**{len(results)} Blogbeiträge gefunden:**\n")
    for r in results:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")
        raw = r.get("raw_content", "")

        # Use raw content if available (more detail), otherwise snippet
        text = raw[:800] if raw else content[:400]

        lines.append(f"### {title}")
        if text:
            lines.append(f"{text}")
        if url:
            lines.append(f"→ {url}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def search_travel_videos(
    query: str,
    max_results: int = 3,
) -> str:
    """Search YouTube travel videos and extract recommendations from transcripts.

    Best for: getting a feel for a route, finding visual highlights,
    discovering stops that bloggers recommend on camera.

    Args:
        query: Search query (e.g. "Sardinia road trip", "Brandenburg Radtour",
               "Basque Country coastal drive")
        max_results: Number of videos to process (1-5, default 3)
    """
    if not query or len(query.strip()) < 3:
        return "Error: query must be at least 3 characters"

    # Search YouTube via Tavily
    search_query = f"site:youtube.com {query} travel vlog route"
    data = await _tavily_search(
        query=search_query[:400],
        max_results=min(max_results, 5),
        search_depth="basic",
    )

    if "error" in data:
        return data["error"]

    results = data.get("results", [])
    if not results:
        return f"Keine Reisevideos gefunden für: {query}"

    lines: list[str] = [f"**{len(results)} Video(s) gefunden:**\n"]

    for r in results:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")

        lines.append(f"### 🎬 {title}")
        if content:
            lines.append(f"{content[:300]}")
        if url:
            lines.append(f"→ {url}")

            # Try to extract transcript
            video_id = None
            if "watch?v=" in url:
                video_id = url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]

            if video_id:
                transcript = await _get_youtube_transcript(video_id)
                if transcript:
                    # Truncate and present
                    lines.append(f"\n**Transkript-Auszug:**\n{transcript[:600]}...")
                else:
                    lines.append("_(Kein Transkript verfügbar)_")

        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def extract_route_tips(
    url: str,
) -> str:
    """Extract structured route tips from a specific travel blog post or article.

    Use after search_travel_blogs to dive deeper into a promising result.
    Extracts: stops, restaurants, accommodations, warnings, highlights.

    Args:
        url: Full URL of the blog post to extract from (must start with http)
    """
    if not url or not url.startswith(("http://", "https://")):
        return "Error: url must start with http:// or https://"

    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY not configured"

    # Extract content via Tavily
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{TAVILY_BASE_URL}/extract",
            json={
                "api_key": TAVILY_API_KEY,
                "urls": [url],
            },
        )

    if response.status_code != 200:
        return f"Error: Tavily API returned {response.status_code}"

    data = response.json()
    results = data.get("results", [])

    if not results:
        return f"Konnte keinen Inhalt extrahieren von: {url}"

    raw_content = results[0].get("raw_content", "")
    if not raw_content:
        return f"Kein Textinhalt gefunden auf: {url}"

    # Truncate very long content
    if len(raw_content) > 8000:
        raw_content = raw_content[:8000] + "\n\n[... gekürzt]"

    return f"# Inhalt von {url}\n\n{raw_content}"


if __name__ == "__main__":
    mcp.run()
