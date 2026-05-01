"""Integration tests for the BRouter MCP server using respx mocks.

These tests exercise the full tool functions (calculate_route, search_location)
with mocked HTTP backends, verifying end-to-end behavior including metadata
extraction, error handling, rate limiting, and header compliance.
"""

import asyncio
import time

import httpx
import respx

from server import (
    BROUTER_BASE_URL,
    NOMINATIM_BASE_URL,
    NOMINATIM_USER_AGENT,
    NominatimRateLimiter,
    calculate_route,
    call_nominatim,
    search_location,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_brouter_gpx(
    track_length: int = 42350,
    filtered_ascend: int = 312,
) -> str:
    """Build a realistic BRouter GPX response string."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="BRouter-1.7.0" '
        'xmlns="http://www.topografix.com/GPX/1/1">\n'
        f'<!-- track-length = "{track_length}" '
        f'filtered ascend = "{filtered_ascend}" -->\n'
        "  <trk><trkseg>"
        '    <trkpt lat="52.5" lon="13.4"><ele>34</ele></trkpt>'
        '    <trkpt lat="52.6" lon="13.5"><ele>45</ele></trkpt>'
        "  </trkseg></trk>\n"
        "</gpx>"
    )


_SAMPLE_GEOJSON = (
    '{"type":"FeatureCollection","features":[{"type":"Feature",'
    '"geometry":{"type":"LineString","coordinates":[[13.4,52.5],[13.5,52.6]]}}]}'
)

_WAYPOINTS = [[13.4, 52.5], [13.5, 52.6]]


# ---------------------------------------------------------------------------
# BRouter integration tests
# ---------------------------------------------------------------------------


@respx.mock
def test_brouter_gpx_returns_metadata_and_content() -> None:
    """BRouter API returns GPX → tool returns route metadata + GPX content."""
    gpx = _make_brouter_gpx(track_length=42350, filtered_ascend=312)
    respx.get(BROUTER_BASE_URL).mock(
        return_value=httpx.Response(200, text=gpx)
    )

    result = asyncio.run(calculate_route(waypoints=_WAYPOINTS))

    # Metadata section
    assert "## Route Summary" in result
    assert "42.4 km" in result  # 42350 m → 42.4 km
    assert "312 m" in result  # filtered ascend
    assert "Estimated duration:" in result
    assert "Profile: trekking" in result
    assert "Format: gpx" in result

    # GPX content section
    assert "## GPX Data" in result
    assert "<trk>" in result or "<trk " in result
    assert "<trkpt" in result


@respx.mock
def test_brouter_geojson_returns_geojson_content() -> None:
    """BRouter API returns GeoJSON → tool returns GeoJSON content."""
    respx.get(BROUTER_BASE_URL).mock(
        return_value=httpx.Response(200, text=_SAMPLE_GEOJSON)
    )

    result = asyncio.run(calculate_route(
        waypoints=_WAYPOINTS,
        format="geojson",
    ))

    assert "## Route (GeoJSON)" in result
    assert "FeatureCollection" in result
    assert "LineString" in result


@respx.mock
def test_brouter_http_500_returns_error_with_status_and_body() -> None:
    """BRouter API returns HTTP 500 → tool returns error with status code and body."""
    error_body = "Internal routing error: segment not found"
    respx.get(BROUTER_BASE_URL).mock(
        return_value=httpx.Response(500, text=error_body)
    )

    result = asyncio.run(calculate_route(waypoints=_WAYPOINTS))

    assert "500" in result
    assert error_body in result


@respx.mock
def test_brouter_timeout_returns_unavailable_error() -> None:
    """BRouter API timeout → tool returns 'unavailable' error."""
    respx.get(BROUTER_BASE_URL).mock(side_effect=httpx.ReadTimeout("timed out"))

    result = asyncio.run(calculate_route(waypoints=_WAYPOINTS))

    assert "unavailable" in result.lower()
    assert "brouter" in result.lower()


# ---------------------------------------------------------------------------
# Nominatim integration tests
# ---------------------------------------------------------------------------


@respx.mock
def test_nominatim_returns_formatted_locations_with_lon_lat_order() -> None:
    """Nominatim returns results → tool returns formatted locations with [lon, lat] order."""
    nominatim_response = [
        {
            "name": "Potsdam Hauptbahnhof",
            "lon": "13.0665",
            "lat": "52.3913",
            "display_name": "Potsdam Hauptbahnhof, Babelsberger Straße, Potsdam, Brandenburg, Deutschland",
        },
        {
            "name": "Potsdam Pirschheide",
            "lon": "13.0134",
            "lat": "52.3802",
            "display_name": "Potsdam Pirschheide, Potsdam, Brandenburg, Deutschland",
        },
    ]
    respx.get(NOMINATIM_BASE_URL).mock(
        return_value=httpx.Response(200, json=nominatim_response)
    )

    result = asyncio.run(search_location(query="Potsdam Hauptbahnhof"))

    assert "## Search Results" in result
    assert "Potsdam Hauptbahnhof" in result

    # Coordinates must be [lon, lat] — longitude first
    assert "[13.0665, 52.3913]" in result
    assert "[13.0134, 52.3802]" in result

    # Numbered results
    assert "1." in result
    assert "2." in result


@respx.mock
def test_nominatim_empty_results_returns_no_locations_found() -> None:
    """Nominatim returns empty results → tool returns 'no locations found'."""
    respx.get(NOMINATIM_BASE_URL).mock(
        return_value=httpx.Response(200, json=[])
    )

    result = asyncio.run(search_location(query="xyznonexistent"))

    assert "no locations found" in result.lower()
    assert "xyznonexistent" in result


def test_nominatim_rate_limiter_enforces_one_second_spacing() -> None:
    """Nominatim rate limiter enforces minimum 1-second spacing between requests."""
    limiter = NominatimRateLimiter()

    async def _run() -> float:
        await limiter.acquire()
        t1 = time.monotonic()
        await limiter.acquire()
        t2 = time.monotonic()
        return t2 - t1

    elapsed = asyncio.run(_run())

    # The second acquire() should have waited ~1 second
    assert elapsed >= 0.95, (
        f"Expected at least ~1s between acquires, got {elapsed:.3f}s"
    )


@respx.mock
def test_nominatim_sends_correct_user_agent_header() -> None:
    """HTTP client sends correct User-Agent header to Nominatim."""
    route = respx.get(NOMINATIM_BASE_URL).mock(
        return_value=httpx.Response(200, json=[])
    )

    params = {
        "q": "Berlin",
        "format": "jsonv2",
        "countrycodes": "de",
        "limit": "5",
    }
    asyncio.run(call_nominatim(params))

    assert route.called
    request = route.calls[0].request
    user_agent = request.headers.get("user-agent", "")
    assert user_agent == NOMINATIM_USER_AGENT, (
        f"Expected User-Agent '{NOMINATIM_USER_AGENT}', got '{user_agent}'"
    )
