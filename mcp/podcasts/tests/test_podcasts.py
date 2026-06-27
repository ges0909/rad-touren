"""Tests for the podcasts MCP client module."""

import pytest
import respx
from httpx import Response
from podcasts import (
    _parse_srt,
    _parse_vtt,
    fetch_transcript,
    get_episodes_from_feed,
    search_podcasts,
)


class TestParseSrt:
    def test_basic_srt(self):
        srt = (
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "Hello and welcome to our travel podcast.\n"
            "\n"
            "2\n"
            "00:00:05,500 --> 00:00:10,000\n"
            "Today we explore the Basque Country.\n"
        )
        result = _parse_srt(srt)
        assert "Hello and welcome" in result
        assert "Basque Country" in result
        assert "-->" not in result

    def test_empty_srt(self):
        assert _parse_srt("") == ""


class TestParseVtt:
    def test_basic_vtt(self):
        vtt = (
            "WEBVTT\n"
            "\n"
            "00:00:01.000 --> 00:00:05.000\n"
            "Welcome to our show.\n"
            "\n"
            "00:00:05.500 --> 00:00:10.000\n"
            "Let's talk about Sardinia.\n"
        )
        result = _parse_vtt(vtt)
        assert "Welcome to our show" in result
        assert "Sardinia" in result
        assert "WEBVTT" not in result
        assert "-->" not in result


class TestSearchPodcasts:
    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_search(self):
        respx.get("https://itunes.apple.com/search").mock(
            return_value=Response(
                200,
                json={
                    "resultCount": 1,
                    "results": [
                        {
                            "collectionId": 12345,
                            "collectionName": "Reise Podcast",
                            "artistName": "Tester",
                            "genres": ["Travel"],
                            "trackCount": 50,
                            "feedUrl": "https://example.com/feed.xml",
                        }
                    ],
                },
            )
        )

        result = await search_podcasts("reise")
        assert result["resultCount"] == 1
        assert result["results"][0]["collectionName"] == "Reise Podcast"

    @respx.mock
    @pytest.mark.asyncio
    async def test_timeout(self):
        import httpx as _httpx

        respx.get("https://itunes.apple.com/search").mock(side_effect=_httpx.ReadTimeout("timeout"))
        result = await search_podcasts("test")
        assert "error" in result
        assert "timed out" in result["error"]


class TestGetEpisodesFromFeed:
    @respx.mock
    @pytest.mark.asyncio
    async def test_parse_rss_feed(self):
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"
             xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
             xmlns:podcast="https://podcastindex.org/namespace/1.0">
          <channel>
            <title>Test Podcast</title>
            <item>
              <title>Episode about Spain</title>
              <description>Tips for a road trip in Northern Spain</description>
              <pubDate>Mon, 15 Jan 2025 10:00:00 GMT</pubDate>
              <itunes:duration>00:45:30</itunes:duration>
              <podcast:transcript url="https://example.com/transcript.srt" type="application/srt"/>
            </item>
            <item>
              <title>Episode about Italy</title>
              <description>Exploring Sardinia by car</description>
              <pubDate>Mon, 08 Jan 2025 10:00:00 GMT</pubDate>
              <itunes:duration>00:38:15</itunes:duration>
            </item>
          </channel>
        </rss>"""

        respx.get("https://example.com/feed.xml").mock(return_value=Response(200, text=rss_xml))

        result = await get_episodes_from_feed("https://example.com/feed.xml")
        assert "error" not in result
        assert result["podcast_title"] == "Test Podcast"
        assert len(result["episodes"]) == 2

        # First episode has transcript
        ep1 = result["episodes"][0]
        assert ep1["title"] == "Episode about Spain"
        assert ep1["transcript_url"] == "https://example.com/transcript.srt"
        assert ep1["duration"] == "00:45:30"

        # Second episode has no transcript
        ep2 = result["episodes"][1]
        assert ep2["title"] == "Episode about Italy"
        assert "transcript_url" not in ep2

    @pytest.mark.asyncio
    async def test_invalid_url(self):
        result = await get_episodes_from_feed("not-a-url")
        assert "error" in result


class TestFetchTranscript:
    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_srt_transcript(self):
        srt_content = "1\n00:00:01,000 --> 00:00:05,000\nHello travelers.\n"
        respx.get("https://example.com/transcript.srt").mock(
            return_value=Response(
                200,
                text=srt_content,
                headers={"content-type": "application/srt"},
            )
        )

        result = await fetch_transcript("https://example.com/transcript.srt")
        assert "error" not in result
        assert "Hello travelers" in result["text"]
        assert result["format"] == "srt"

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_vtt_transcript(self):
        vtt_content = "WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nWillkommen auf unserer Reise.\n"
        respx.get("https://example.com/transcript.vtt").mock(
            return_value=Response(
                200,
                text=vtt_content,
                headers={"content-type": "text/vtt"},
            )
        )

        result = await fetch_transcript("https://example.com/transcript.vtt")
        assert "error" not in result
        assert "Willkommen auf unserer Reise" in result["text"]
        assert result["format"] == "vtt"

    @pytest.mark.asyncio
    async def test_invalid_url(self):
        result = await fetch_transcript("not-a-url")
        assert "error" in result
