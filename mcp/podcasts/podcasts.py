"""Pure HTTP client logic for podcast search and transcript retrieval.

No FastMCP dependency — importable independently for testing.
Uses the iTunes Search API (no auth needed) for podcast/episode discovery,
RSS feed parsing for episode details, and Podcasting 2.0 transcript tags
for transcript retrieval.

No API key required.
"""

import json
import xml.etree.ElementTree as ET

import httpx

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"
USER_AGENT = "gerrit-on-tour-mcp/1.0"

# Podcast namespace URIs (Podcasting 2.0)
PODCAST_NS = {
    "podcast": "https://podcastindex.org/namespace/1.0",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
}


async def search_podcasts(query: str, max_results: int = 10, country: str = "de") -> dict:
    """Search podcasts via iTunes Search API.

    Returns {"results": [...], "resultCount": N} or {"error": "..."}.
    """
    params = {
        "term": query,
        "media": "podcast",
        "entity": "podcast",
        "limit": max_results,
        "country": country,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                ITUNES_SEARCH_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
            )
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}

    if response.status_code != 200:
        return {"error": f"iTunes API returned {response.status_code}"}

    return response.json()


async def search_episodes(query: str, max_results: int = 10, country: str = "de") -> dict:
    """Search podcast episodes via iTunes Search API.

    Returns {"results": [...], "resultCount": N} or {"error": "..."}.
    """
    params = {
        "term": query,
        "media": "podcast",
        "entity": "podcastEpisode",
        "limit": max_results,
        "country": country,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                ITUNES_SEARCH_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
            )
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}

    if response.status_code != 200:
        return {"error": f"iTunes API returned {response.status_code}"}

    return response.json()


async def get_episodes_from_feed(feed_url: str, max_results: int = 20) -> dict:
    """Parse an RSS feed to get episodes with transcript info.

    Returns {"episodes": [...], "podcast_title": "..."} or {"error": "..."}.
    """
    if not feed_url or not feed_url.startswith(("http://", "https://")):
        return {"error": "Invalid feed URL"}

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                feed_url,
                headers={"User-Agent": USER_AGENT},
            )
    except httpx.TimeoutException:
        return {"error": "Feed fetch timed out"}
    except httpx.RequestError as e:
        return {"error": f"Feed fetch failed: {e}"}

    if response.status_code != 200:
        return {"error": f"Feed returned {response.status_code}"}

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        return {"error": "Failed to parse RSS feed XML"}

    channel = root.find("channel")
    if channel is None:
        return {"error": "No <channel> element found in RSS feed"}

    podcast_title = channel.findtext("title", "Unbekannt")

    episodes: list[dict] = []
    for item in channel.findall("item")[:max_results]:
        ep: dict = {
            "title": item.findtext("title", "Unbekannt"),
            "description": item.findtext("description", ""),
            "pub_date": item.findtext("pubDate", ""),
            "link": item.findtext("link", ""),
            "guid": item.findtext("guid", ""),
        }

        # Get duration from itunes:duration
        duration_elem = item.find("itunes:duration", PODCAST_NS)
        if duration_elem is not None and duration_elem.text:
            ep["duration"] = duration_elem.text

        # Get enclosure (audio URL)
        enclosure = item.find("enclosure")
        if enclosure is not None:
            ep["audio_url"] = enclosure.get("url", "")

        # Get transcript (Podcasting 2.0)
        transcript_elem = item.find("podcast:transcript", PODCAST_NS)
        if transcript_elem is not None:
            ep["transcript_url"] = transcript_elem.get("url", "")
            ep["transcript_type"] = transcript_elem.get("type", "")

        episodes.append(ep)

    return {"episodes": episodes, "podcast_title": podcast_title}


async def lookup_podcast_feed_url(collection_id: int) -> dict:
    """Look up a podcast's feed URL by its iTunes collection ID.

    Returns {"feedUrl": "...", "collectionName": "..."} or {"error": "..."}.
    """
    params = {"id": collection_id, "entity": "podcast"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                ITUNES_LOOKUP_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
            )
    except httpx.TimeoutException:
        return {"error": "Request timed out"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}

    if response.status_code != 200:
        return {"error": f"iTunes API returned {response.status_code}"}

    data = response.json()
    results = data.get("results", [])
    if not results:
        return {"error": f"No podcast found for ID {collection_id}"}

    podcast = results[0]
    feed_url = podcast.get("feedUrl", "")
    if not feed_url:
        return {"error": "Podcast has no public feed URL"}

    return {
        "feedUrl": feed_url,
        "collectionName": podcast.get("collectionName", ""),
        "collectionId": podcast.get("collectionId", collection_id),
    }


async def fetch_transcript(transcript_url: str) -> dict:
    """Fetch a transcript from a Podcasting 2.0 transcript URL.

    Supports SRT, VTT, JSON, and plain text formats.
    Returns {"text": "...", "format": "..."} or {"error": "..."}.
    """
    if not transcript_url or not transcript_url.startswith(("http://", "https://")):
        return {"error": "Invalid transcript URL"}

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                transcript_url,
                headers={"User-Agent": USER_AGENT},
            )
    except httpx.TimeoutException:
        return {"error": "Transcript fetch timed out"}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {e}"}

    if response.status_code != 200:
        return {"error": f"Transcript URL returned {response.status_code}"}

    content_type = response.headers.get("content-type", "")
    text = response.text

    # Detect format
    if "application/srt" in content_type or transcript_url.endswith(".srt"):
        fmt = "srt"
        text = _parse_srt(text)
    elif "text/vtt" in content_type or transcript_url.endswith(".vtt"):
        fmt = "vtt"
        text = _parse_vtt(text)
    elif "application/json" in content_type or transcript_url.endswith(".json"):
        fmt = "json"
        text = _parse_json_transcript(text)
    else:
        fmt = "text"

    # Truncate very long transcripts
    if len(text) > 15000:
        text = text[:15000] + "\n\n[... gekürzt, Transkript zu lang]"

    return {"text": text, "format": fmt}


def _parse_srt(raw: str) -> str:
    """Extract plain text from SRT subtitle format."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        # Skip sequence numbers, timestamps, and empty lines
        if not line or line.isdigit() or "-->" in line:
            continue
        lines.append(line)
    return " ".join(lines)


def _parse_vtt(raw: str) -> str:
    """Extract plain text from WebVTT format."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        # Skip header, timestamps, empty lines, and metadata
        if not line or line.startswith("WEBVTT") or "-->" in line or line.startswith("NOTE"):
            continue
        # Skip cue identifiers (lines that are just numbers)
        if line.isdigit():
            continue
        lines.append(line)
    return " ".join(lines)


def _parse_json_transcript(raw: str) -> str:
    """Extract plain text from JSON transcript format (Podcasting 2.0)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    # Handle Podcasting 2.0 JSON transcript format
    if isinstance(data, dict) and "segments" in data:
        segments = data["segments"]
        return " ".join(s.get("body", "") for s in segments if s.get("body"))

    # Alternative: list of segments
    if isinstance(data, list):
        return " ".join(
            item.get("body", "") or item.get("text", "") for item in data if isinstance(item, dict)
        )

    return raw
