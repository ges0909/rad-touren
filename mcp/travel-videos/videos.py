"""Pure HTTP client logic for travel video search and transcript extraction.

No FastMCP dependency — importable independently for testing.
Searches public broadcaster (ÖR) content on YouTube and ARD/ZDF mediatheks.
Uses youtube-transcript-api for transcript extraction.
"""

import asyncio
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com"

# German public broadcaster names — always appended to searches so results
# come from ÖR channels (WDR Reisen, ARD Reisen, NDR, BR, SWR, MDR, ZDF)
# rather than private travel vlogs.
_OER_TERMS = "WDR NDR ARD BR SWR MDR ZDF"

# Domains to search: YouTube (ÖR channels live here) + major mediatheks
_OER_DOMAINS = ["youtube.com", "ardmediathek.de", "zdf.de", "ndr.de", "br.de"]

# Activity-specific documentary terms that work well with ÖR channel names
_ACTIVITY_KEYWORDS: dict[str, str] = {
    "cycling": "Radtour Fahrradreise Doku",
    "roadtrip": "Roadtrip Reisereportage Doku",
    "hiking": "Wanderung Wanderdoku Reportage",
    "bikepacking": "Bikepacking Radreise Doku",
}


def extract_video_id(url: str) -> str | None:
    """Extract the 11-character YouTube video ID from any common URL format."""
    patterns = [
        r"[?&]v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"/embed/([a-zA-Z0-9_-]{11})",
        r"/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


async def search_youtube_videos(
    query: str,
    region: str = "",
    activity: str = "",
    max_results: int = 5,
) -> dict:
    """Search public broadcaster (ÖR) travel videos via Tavily.

    Targets WDR, NDR, ARD, BR, SWR, MDR, ZDF on YouTube and mediatheks.
    Returns a dict with a "videos" list or {"error": "..."} on failure.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}

    terms = [query]
    if region:
        terms.append(region)
    if activity in _ACTIVITY_KEYWORDS:
        terms.append(_ACTIVITY_KEYWORDS[activity])
    # Always add ÖR broadcaster names to filter for public TV content
    terms.append(_OER_TERMS)

    search_query = " ".join(terms)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{TAVILY_BASE_URL}/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": search_query[:400],
                    "max_results": min(max_results, 10),
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_domains": _OER_DOMAINS,
                },
            )
    except httpx.TimeoutException:
        return {"error": "Search request timed out"}

    if resp.status_code != 200:
        return {"error": f"Tavily API returned {resp.status_code}"}

    videos = []
    for r in resp.json().get("results", []):
        url = r.get("url", "")
        video_id = extract_video_id(url)
        entry = {
            "title": r.get("title", ""),
            "url": url,
            "video_id": video_id,
            "description": r.get("content", "")[:300],
            "published_date": r.get("published_date", ""),
            "source": "youtube" if video_id else "mediathek",
        }
        is_mediathek = any(d in url for d in ["ardmediathek.de", "zdf.de", "ndr.de", "br.de"])
        if video_id or is_mediathek:
            videos.append(entry)

    return {"videos": videos, "query": search_query}


def _get_transcript_sync(video_id: str, languages: list[str]) -> dict:
    """Fetch a YouTube transcript synchronously — run via asyncio.to_thread.

    Compatible with youtube-transcript-api >= 1.0 (instance-based API).
    """
    try:
        from youtube_transcript_api import (  # noqa: PLC0415
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError:
        return {"error": "youtube-transcript-api is not installed"}

    def _join(raw: list) -> str:
        return " ".join(
            seg["text"] if isinstance(seg, dict) else getattr(seg, "text", "") for seg in raw
        ).strip()

    api = YouTubeTranscriptApi()

    try:
        fetched = api.fetch(video_id, languages=languages)
        raw = fetched.to_raw_data()
        return {"transcript": _join(raw), "segment_count": len(raw)}

    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video"}

    except NoTranscriptFound:
        # Fallback: pick any available transcript (prefer manual over auto-generated)
        try:
            transcript_list = api.list(video_id)
            available = list(transcript_list)
            if not available:
                return {"error": "No transcripts available for this video"}
            manual = [t for t in available if not t.is_generated]
            chosen = manual[0] if manual else available[0]
            raw = chosen.fetch().to_raw_data()
            return {
                "transcript": _join(raw),
                "segment_count": len(raw),
                "language": chosen.language_code,
                "note": (
                    f"Requested language(s) {languages} not available — "
                    f"used '{chosen.language}' instead"
                ),
            }
        except Exception as exc:
            return {"error": f"No transcript available: {exc}"}

    except Exception as exc:
        return {"error": str(exc)}


async def get_transcript(video_id: str, languages: list[str] | None = None) -> dict:
    """Fetch a YouTube transcript asynchronously.

    Returns dict with "transcript" (str) and "segment_count" (int),
    or {"error": "..."} on failure.
    """
    if languages is None:
        languages = ["de", "en"]
    return await asyncio.to_thread(_get_transcript_sync, video_id, languages)
