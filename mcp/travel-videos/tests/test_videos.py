"""Tests for the travel-videos client module (videos.py).

Covers:
- extract_video_id  — pure function, no network
- search_youtube_videos — Tavily HTTP, mocked with respx
- _get_transcript_sync  — YouTubeTranscriptApi, mocked via sys.modules
- get_transcript         — async wrapper around _get_transcript_sync
"""

import sys
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from videos import _get_transcript_sync, extract_video_id, get_transcript, search_youtube_videos

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VIDEO_ID = "dQw4w9WgXcQ"  # 11-char test ID


def _fake_yt_module(
    segments: list | None = None,
    raises_disabled: bool = False,
    raises_not_found: bool = False,
    fallback_segments: list | None = None,
) -> MagicMock:
    """Build a fake youtube_transcript_api module for sys.modules injection.

    Compatible with youtube-transcript-api v1.x (instance-based API):
      api = YouTubeTranscriptApi()
      fetched = api.fetch(video_id, languages=...)
      raw = fetched.to_raw_data()  -> List[Dict]
    """

    class FakeTranscriptsDisabled(Exception):
        pass

    class FakeNoTranscriptFound(Exception):
        pass

    # Mock FetchedTranscript returned by api.fetch()
    mock_fetched = MagicMock()
    mock_fetched.to_raw_data.return_value = segments or []

    # Mock api instance (what YouTubeTranscriptApi() returns)
    api_instance = MagicMock()

    if raises_disabled:
        api_instance.fetch.side_effect = FakeTranscriptsDisabled()
    elif raises_not_found:
        api_instance.fetch.side_effect = FakeNoTranscriptFound()
        if fallback_segments is not None:
            fallback_fetched = MagicMock()
            fallback_fetched.to_raw_data.return_value = fallback_segments
            fallback_transcript = MagicMock()
            fallback_transcript.is_generated = False
            fallback_transcript.language = "English"
            fallback_transcript.language_code = "en"
            fallback_transcript.fetch.return_value = fallback_fetched
            api_instance.list.return_value = [fallback_transcript]
        else:
            api_instance.list.return_value = []
    else:
        api_instance.fetch.return_value = mock_fetched

    # Mock class — when called as YouTubeTranscriptApi(), returns api_instance
    mock_api_class = MagicMock(return_value=api_instance)

    mod = MagicMock()
    mod.YouTubeTranscriptApi = mock_api_class
    mod.TranscriptsDisabled = FakeTranscriptsDisabled
    mod.NoTranscriptFound = FakeNoTranscriptFound
    return mod


# ---------------------------------------------------------------------------
# extract_video_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        (f"https://www.youtube.com/watch?v={VIDEO_ID}", VIDEO_ID),
        (f"https://youtu.be/{VIDEO_ID}", VIDEO_ID),
        (f"https://www.youtube.com/embed/{VIDEO_ID}", VIDEO_ID),
        (f"https://www.youtube.com/shorts/{VIDEO_ID}", VIDEO_ID),
        (f"https://www.youtube.com/watch?v={VIDEO_ID}&list=PLxxx&t=42s", VIDEO_ID),
        ("https://www.youtube.com/channel/UCsomething", None),
        ("https://vimeo.com/123456789", None),
        ("", None),
    ],
)
def test_extract_video_id(url: str, expected: str | None) -> None:
    assert extract_video_id(url) == expected


# ---------------------------------------------------------------------------
# search_youtube_videos
# ---------------------------------------------------------------------------


async def test_search_no_api_key(monkeypatch) -> None:
    monkeypatch.setattr("videos.TAVILY_API_KEY", "")
    result = await search_youtube_videos("Spreewald Radtour")
    assert "error" in result


@respx.mock
async def test_search_returns_videos(monkeypatch) -> None:
    monkeypatch.setattr("videos.TAVILY_API_KEY", "test-key")
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Spreewald Radtour 2024",
                        "url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
                        "content": "Tolle Tour durch den Spreewald",
                        "published_date": "2024-06-01",
                    },
                    # Non-YouTube result — must be filtered out
                    {
                        "title": "Some blog post",
                        "url": "https://example.com/blog",
                        "content": "Not a video",
                        "published_date": "",
                    },
                ]
            },
        )
    )
    result = await search_youtube_videos(
        "Spreewald Radtour", region="Brandenburg", activity="cycling"
    )
    assert "error" not in result
    assert len(result["videos"]) == 1
    assert result["videos"][0]["video_id"] == VIDEO_ID
    assert result["videos"][0]["title"] == "Spreewald Radtour 2024"


@respx.mock
async def test_search_tavily_server_error(monkeypatch) -> None:
    monkeypatch.setattr("videos.TAVILY_API_KEY", "test-key")
    respx.post("https://api.tavily.com/search").mock(return_value=httpx.Response(500))
    result = await search_youtube_videos("test")
    assert "error" in result
    assert "500" in result["error"]


@respx.mock
async def test_search_empty_results(monkeypatch) -> None:
    monkeypatch.setattr("videos.TAVILY_API_KEY", "test-key")
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    result = await search_youtube_videos("obscure query no results")
    assert result["videos"] == []


# ---------------------------------------------------------------------------
# _get_transcript_sync
# ---------------------------------------------------------------------------


def test_transcript_sync_success(monkeypatch) -> None:
    segments = [
        {"text": "Hallo und willkommen", "start": 0.0, "duration": 2.0},
        {"text": "zur Spreewald Radtour", "start": 2.0, "duration": 2.5},
    ]
    monkeypatch.setitem(sys.modules, "youtube_transcript_api", _fake_yt_module(segments=segments))
    result = _get_transcript_sync(VIDEO_ID, ["de", "en"])
    assert "error" not in result
    assert result["transcript"] == "Hallo und willkommen zur Spreewald Radtour"
    assert result["segment_count"] == 2


def test_transcript_sync_transcripts_disabled(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules, "youtube_transcript_api", _fake_yt_module(raises_disabled=True)
    )
    result = _get_transcript_sync(VIDEO_ID, ["de"])
    assert "error" in result
    assert "disabled" in result["error"].lower()


def test_transcript_sync_fallback_language(monkeypatch) -> None:
    fallback = [
        {"text": "Hello", "start": 0.0, "duration": 2.0},
        {"text": "world", "start": 2.0, "duration": 2.0},
    ]
    monkeypatch.setitem(
        sys.modules,
        "youtube_transcript_api",
        _fake_yt_module(raises_not_found=True, fallback_segments=fallback),
    )
    result = _get_transcript_sync(VIDEO_ID, ["de"])
    assert "error" not in result
    assert result["transcript"] == "Hello world"
    assert result["language"] == "en"
    assert "note" in result


def test_transcript_sync_no_transcripts_at_all(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "youtube_transcript_api",
        _fake_yt_module(raises_not_found=True, fallback_segments=None),
    )
    result = _get_transcript_sync(VIDEO_ID, ["de"])
    assert "error" in result


# ---------------------------------------------------------------------------
# get_transcript (async wrapper)
# ---------------------------------------------------------------------------


async def test_get_transcript_async_delegates_to_sync() -> None:
    expected = {"transcript": "test content", "segment_count": 5}
    with patch("videos._get_transcript_sync", return_value=expected):
        result = await get_transcript(VIDEO_ID, ["de", "en"])
    assert result == expected
