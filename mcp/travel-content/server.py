"""MCP server for extracting structured travel recommendations from blogs and videos.

Searches curated travel blog sources and YouTube transcripts, then extracts
actionable route planning data: stops, highlights, warnings, restaurant tips.

Requires TAVILY_API_KEY environment variable for web search.

Usage:
    python server.py
"""

from content import (
    get_source_domains,
    get_youtube_transcript,
    tavily_extract,
    tavily_search,
)
from fastmcp import FastMCP

mcp = FastMCP("Travel Content")


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_travel_articles(
    query: str,
    region: str = "",
    activity: str = "roadtrip",
    max_results: int = 5,
) -> str:
    """Search quality travel journalism for route recommendations and destination tips.

    Searches established newspapers, travel magazines, and public broadcaster
    websites (Spiegel, Zeit, GEO, Merian, National Geographic, Guardian, NDR,
    BR, SWR etc.) — not random blogs.

    Args:
        query: Search query (e.g. "Nordspanien Küste Roadtrip Tipps",
               "Brandenburg Radtour Seen", "Sardinien beste Strände")
        region: Region to focus on (e.g. "spain", "italy", "brandenburg").
                Adds region-specific quality sources.
        activity: Type of travel — "roadtrip", "cycling", "bikepacking", "hiking"
        max_results: Number of articles to return (1-10, default 5)
    """
    if not query or len(query.strip()) < 3:
        return "Error: query must be at least 3 characters"

    domains = get_source_domains(region, activity)
    search_query = f"{query} {activity} Reportage Reisebericht"

    data = await tavily_search(
        query=search_query[:400],
        max_results=min(max_results, 10),
        include_domains=domains if domains else None,
        search_depth="advanced",
    )

    if "error" in data:
        return f"Error: {data['error']}"

    answer = data.get("answer")
    results = data.get("results", [])
    if not results:
        return f"Keine Artikel gefunden für: {query}"

    lines: list[str] = []
    if answer:
        lines.append(f"**Zusammenfassung:** {answer}\n")

    lines.append(f"**{len(results)} Artikel gefunden:**\n")
    for r in results:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        raw = r.get("raw_content", "")
        content = r.get("content", "")
        text = raw[:800] if raw else content[:400]

        lines.append(f"### {title}")
        if text:
            lines.append(text)
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
    data = await tavily_search(
        query=search_query[:400],
        max_results=min(max_results, 5),
        search_depth="basic",
        include_raw_content=False,
    )

    if "error" in data:
        return f"Error: {data['error']}"

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
                transcript = await get_youtube_transcript(video_id)
                if transcript:
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
    data = await tavily_extract(url)

    if "error" in data:
        return f"Error: {data['error']}"

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
