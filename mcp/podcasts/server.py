"""MCP server for searching travel-related podcasts and extracting episode transcripts.

Uses the iTunes Search API (no authentication required) for podcast discovery,
RSS feed parsing for episode details, and Podcasting 2.0 transcript tags
for transcript retrieval.

No API key required.

Usage:
    python server.py
"""

import re

from fastmcp import FastMCP
from podcasts import (
    fetch_transcript as _fetch_transcript,
)
from podcasts import (
    get_episodes_from_feed as _get_episodes_from_feed,
)
from podcasts import (
    lookup_podcast_feed_url as _lookup_podcast_feed_url,
)
from podcasts import (
    search_episodes as _search_episodes,
)
from podcasts import (
    search_podcasts as _search_podcasts,
)

mcp = FastMCP("Podcasts")


@mcp.tool()
async def search_podcasts(
    query: str,
    max_results: int = 10,
) -> str:
    """Search for podcasts by name, topic, or region.

    Best for finding travel podcasts about specific destinations or travel styles.
    Returns podcast titles, descriptions, and feed IDs for further exploration.

    Args:
        query: Search query (e.g. "Reise Spanien", "road trip Europe",
               "Radreise Deutschland", "Nordspanien Küste")
        max_results: Maximum number of results to return (1-20, default 10)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"

    max_results = max(1, min(max_results, 20))

    data = await _search_podcasts(query, max_results)

    if "error" in data:
        return f"Error: {data['error']}"

    results = data.get("results", [])
    if not results:
        return f"Keine Podcasts gefunden für: {query}"

    count = data.get("resultCount", len(results))
    lines: list[str] = [f'**{count} Podcast(s) gefunden für "{query}":**\n']

    for pod in results:
        name = pod.get("collectionName", "Unbekannt")
        artist = pod.get("artistName", "")
        genre = ", ".join(pod.get("genres", []))
        track_count = pod.get("trackCount", 0)
        collection_id = pod.get("collectionId", "")
        feed_url = pod.get("feedUrl", "")

        lines.append(f"### {name}")
        if artist:
            lines.append(f"**Autor:** {artist}")
        if genre:
            lines.append(f"**Genre:** {genre}")
        if track_count:
            lines.append(f"**Episoden:** {track_count}")
        if collection_id:
            lines.append(f"**Feed-ID:** {collection_id}")
        if feed_url:
            lines.append(f"**Feed:** {feed_url}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def search_podcast_episodes(
    query: str,
    max_results: int = 10,
) -> str:
    """Search for podcast episodes across all podcasts by keyword.

    Best for finding specific episodes about a travel destination, route,
    or topic. Returns episode titles, descriptions, and transcript availability.

    Args:
        query: Search query (e.g. "Baskenland Roadtrip", "Sardinien Geheimtipps",
               "cycling Brandenburg", "Küstenstraße Spanien")
        max_results: Number of results to return (1-20, default 10)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"

    max_results = max(1, min(max_results, 20))

    data = await _search_episodes(query, max_results)

    if "error" in data:
        return f"Error: {data['error']}"

    results = data.get("results", [])
    if not results:
        return f"Keine Episoden gefunden für: {query}"

    count = data.get("resultCount", len(results))
    lines: list[str] = [f'**{count} Episode(n) gefunden für "{query}":**\n']

    for ep in results:
        track_name = ep.get("trackName", "Unbekannt")
        collection_name = ep.get("collectionName", "")
        description = ep.get("description", "") or ep.get("shortDescription", "")
        release_date = ep.get("releaseDate", "")[:10]
        duration_ms = ep.get("trackTimeMillis", 0)
        collection_id = ep.get("collectionId", "")

        # Format duration
        duration_str = ""
        if duration_ms:
            mins = duration_ms // 60000
            duration_str = f" ({mins} Min.)"

        lines.append(f"### {track_name}{duration_str}")
        if collection_name:
            lines.append(f"**Podcast:** {collection_name}")
        if release_date:
            lines.append(f"**Datum:** {release_date}")
        if description:
            clean_desc = re.sub(r"<[^>]+>", "", description)
            lines.append(f"{clean_desc[:300]}")
        if collection_id:
            lines.append(
                f"**Feed-ID:** {collection_id} _(verwende get_podcast_episodes für Details)_"
            )
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_podcast_episodes(
    feed_id: int,
    max_results: int = 15,
) -> str:
    """Get episodes from a specific podcast feed.

    Use after search_podcasts to explore episodes of a promising podcast.
    Shows which episodes have transcripts available.

    Args:
        feed_id: Podcast feed ID (from search_podcasts results)
        max_results: Number of episodes to return (1-30, default 15)
    """
    if feed_id <= 0:
        return "Error: feed_id must be a positive integer"

    max_results = max(1, min(max_results, 30))

    # Look up feed URL from iTunes
    lookup = await _lookup_podcast_feed_url(feed_id)
    if "error" in lookup:
        return f"Error: {lookup['error']}"

    feed_url = lookup["feedUrl"]
    collection_name = lookup.get("collectionName", "")

    # Parse RSS feed for episodes
    data = await _get_episodes_from_feed(feed_url, max_results)

    if "error" in data:
        return f"Error: {data['error']}"

    episodes = data.get("episodes", [])
    podcast_title = data.get("podcast_title", collection_name)

    if not episodes:
        return f"Keine Episoden gefunden für: {podcast_title}"

    lines: list[str] = [f'**{len(episodes)} Episode(n) von "{podcast_title}":**\n']

    for ep in episodes:
        title = ep.get("title", "Unbekannt")
        pub_date = ep.get("pub_date", "")
        duration = ep.get("duration", "")
        transcript_url = ep.get("transcript_url", "")

        transcript_badge = " 📝" if transcript_url else ""
        duration_str = f" ({duration})" if duration else ""

        lines.append(f"### {title}{duration_str}{transcript_badge}")
        if pub_date:
            lines.append(f"**Datum:** {pub_date}")

        description = ep.get("description", "")
        if description:
            clean_desc = re.sub(r"<[^>]+>", "", description)
            lines.append(f"{clean_desc[:250]}")

        if transcript_url:
            lines.append("**Transkript verfügbar** ✓")
            lines.append(f"**Transkript-URL:** {transcript_url}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_episode_transcript(
    transcript_url: str,
) -> str:
    """Fetch the transcript of a podcast episode.

    Retrieves the full text transcript if the episode has one available
    (Podcasting 2.0 standard). Supports SRT, VTT, JSON, and plain text formats.

    Args:
        transcript_url: Transcript URL (from get_podcast_episodes results, marked with 📝)
    """
    if not transcript_url or not transcript_url.startswith(("http://", "https://")):
        return "Error: transcript_url must be a valid HTTP(S) URL"

    result = await _fetch_transcript(transcript_url)

    if "error" in result:
        return f"Error beim Abrufen des Transkripts: {result['error']}"

    text = result.get("text", "")
    fmt = result.get("format", "unknown")

    if not text.strip():
        return "Transkript ist leer."

    return f"**Format:** {fmt} | **Länge:** {len(text)} Zeichen\n\n---\n\n{text}"


if __name__ == "__main__":
    mcp.run()
