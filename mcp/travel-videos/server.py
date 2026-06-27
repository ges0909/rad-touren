"""MCP server for searching travel videos and extracting YouTube transcripts.

Searches YouTube for travel content (cycling tours, road trips, hiking) and
retrieves full transcripts for route planning and destination research.

Requires TAVILY_API_KEY in .env for video search.
Transcript extraction uses YouTube public captions — no additional API key needed.

Usage:
    python server.py
"""

from fastmcp import FastMCP
from videos import extract_video_id as _extract_video_id
from videos import get_transcript as _get_transcript
from videos import search_youtube_videos as _search_youtube_videos

mcp = FastMCP("Travel Videos")

# Maximum transcript length per video returned to the agent
_TRANSCRIPT_MAX_CHARS = 4000

# Language → ordered list of YouTube caption language codes to try
_LANG_PREFERENCE: dict[str, list[str]] = {
    "de": ["de", "de-DE", "de-AT", "de-CH", "en"],
    "en": ["en", "en-US", "en-GB", "de"],
}


@mcp.tool()
async def search_travel_videos(
    query: str,
    region: str = "",
    activity: str = "",
    max_results: int = 5,
) -> str:
    """Search public broadcaster (ÖR) videos relevant to route planning.

    Searches YouTube channels of WDR, NDR, ARD, BR, SWR, MDR, ZDF and the
    ARD/ZDF mediatheks. Private travel vlogs are excluded.
    Use get_video_transcript to read the full spoken content of a YouTube result.

    Args:
        query: Search query, e.g. "Spreewald Radtour", "Baskenland Roadtrip",
               "Schottland Küstenweg Wanderung"
        region: Region name to sharpen the search, e.g. "Brandenburg", "Toskana".
        activity: Travel type — "cycling", "roadtrip", "hiking", "bikepacking".
        max_results: Number of videos/mediathek entries to return (1–10, default 5).
    """
    if not query or len(query.strip()) < 3:
        return "Error: query must be at least 3 characters"
    if not 1 <= max_results <= 10:
        return "Error: max_results must be between 1 and 10"

    data = await _search_youtube_videos(
        query=query.strip(),
        region=region.strip(),
        activity=activity.strip(),
        max_results=max_results,
    )

    if "error" in data:
        return f"Error: {data['error']}"

    videos = data.get("videos", [])
    if not videos:
        return f"Keine YouTube-Videos gefunden für: {query}"

    lines = [f"**{len(videos)} ÖR-Video(s) gefunden** — Suche: `{data.get('query', query)}`\n"]
    for i, v in enumerate(videos, 1):
        source_label = "📺 Mediathek" if v.get("source") == "mediathek" else "▶️ YouTube"
        lines.append(f"### {i}. {v['title']} {source_label}")
        if v["description"]:
            lines.append(v["description"])
        if v["published_date"]:
            lines.append(f"📅 {v['published_date']}")
        lines.append(f"🔗 {v['url']}")
        if v.get("source") == "mediathek":
            lines.append("_Transkript nur für YouTube-Videos verfügbar._")
        lines.append("")

    lines.append("---")
    lines.append("_Transkript abrufen mit `get_video_transcript(url=...)`_")
    return "\n".join(lines)


@mcp.tool()
async def get_video_transcript(
    url: str,
    language: str = "de",
) -> str:
    """Fetch the full transcript of a YouTube video.

    Returns the complete spoken content — useful for extracting route stops,
    local tips, restaurant recommendations, and travel warnings.

    Args:
        url: Full YouTube URL (e.g. "https://www.youtube.com/watch?v=abc1234567")
             or a bare 11-character video ID.
        language: Preferred transcript language — "de" (default) or "en".
                  Falls back to any available language if the requested one is absent.
    """
    if not url or not url.strip():
        return "Error: url is required"
    if language not in _LANG_PREFERENCE:
        return f"Error: language must be one of {list(_LANG_PREFERENCE)}"

    url = url.strip()
    is_yt_url = "youtube" in url or "youtu.be" in url
    video_id = _extract_video_id(url) if is_yt_url else url

    if not video_id or len(video_id) != 11:
        return "Error: could not extract a valid YouTube video ID from the provided URL"

    data = await _get_transcript(video_id, _LANG_PREFERENCE[language])

    if "error" in data:
        return f"Kein Transkript verfügbar (Video-ID: `{video_id}`): {data['error']}"

    transcript = data["transcript"]
    note = data.get("note", "")
    segment_count = data.get("segment_count", 0)

    truncated = len(transcript) > _TRANSCRIPT_MAX_CHARS
    if truncated:
        transcript = transcript[:_TRANSCRIPT_MAX_CHARS]

    lines = [f"**Transkript** — Video-ID: `{video_id}` ({segment_count} Segmente)\n"]
    if note:
        lines.append(f"_ℹ️ {note}_\n")
    if truncated:
        lines.append(f"_⚠️ Transkript auf {_TRANSCRIPT_MAX_CHARS} Zeichen gekürzt._\n")
    lines.append(transcript)
    return "\n".join(lines)


@mcp.tool()
async def search_and_transcribe(
    query: str,
    region: str = "",
    activity: str = "",
    max_results: int = 3,
    language: str = "de",
) -> str:
    """Search for travel videos and immediately fetch their transcripts.

    Combines search and transcript extraction in a single call — ideal for
    gathering route planning insights from multiple videos at once.

    Args:
        query: Search query, e.g. "Spreewald Radtour", "Baskenland Roadtrip"
        region: Region name, e.g. "Brandenburg", "Toskana"
        activity: Travel type — "cycling", "roadtrip", "hiking", "bikepacking"
        max_results: Number of videos to process (1–5, default 3). Keep low —
                     each video requires a separate transcript fetch.
        language: Preferred transcript language — "de" (default) or "en"
    """
    if not query or len(query.strip()) < 3:
        return "Error: query must be at least 3 characters"
    if not 1 <= max_results <= 5:
        return "Error: max_results must be between 1 and 5"
    if language not in _LANG_PREFERENCE:
        return f"Error: language must be one of {list(_LANG_PREFERENCE)}"

    search_data = await _search_youtube_videos(
        query=query.strip(),
        region=region.strip(),
        activity=activity.strip(),
        max_results=max_results,
    )

    if "error" in search_data:
        return f"Error: {search_data['error']}"

    videos = search_data.get("videos", [])
    if not videos:
        return f"Keine YouTube-Videos gefunden für: {query}"

    lang_codes = _LANG_PREFERENCE[language]
    lines = [f"# Reisevideos: {query}\n", f"_{len(videos)} Video(s) verarbeitet_\n"]

    for i, v in enumerate(videos, 1):
        lines.append(f"## {i}. {v['title']}")
        lines.append(f"🔗 {v['url']}")
        if v["description"]:
            lines.append(f"_{v['description']}_")
        lines.append("")

        if v.get("source") == "mediathek" or not v.get("video_id"):
            lines.append("_📺 Mediathek-Beitrag — Transkript nur für YouTube-Videos verfügbar._")
        else:
            transcript_data = await _get_transcript(v["video_id"], lang_codes)
            if "error" in transcript_data:
                lines.append(f"_Kein Transkript: {transcript_data['error']}_")
            else:
                transcript = transcript_data["transcript"]
                note = transcript_data.get("note", "")
                if note:
                    lines.append(f"_ℹ️ {note}_")
                if len(transcript) > _TRANSCRIPT_MAX_CHARS:
                    transcript = transcript[:_TRANSCRIPT_MAX_CHARS]
                    lines.append(f"_⚠️ Transkript auf {_TRANSCRIPT_MAX_CHARS} Zeichen gekürzt._")
                lines.append("**Transkript:**")
                lines.append(transcript)

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
