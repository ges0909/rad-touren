"""Tests for overpass-mcp server."""

import httpx
import pytest
import respx
from server import (
    CATEGORY_PRESETS,
    POI_CATEGORIES,
    _build_around_poly,
    _build_query,
    _format_results,
    _sample_track_points,
    search_pois_along_route,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_GPX = """<?xml version='1.0' encoding='utf-8'?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
 <trk><trkseg>
  <trkpt lat="52.52" lon="13.40"><ele>34</ele></trkpt>
  <trkpt lat="52.53" lon="13.41"><ele>35</ele></trkpt>
  <trkpt lat="52.54" lon="13.42"><ele>36</ele></trkpt>
  <trkpt lat="52.55" lon="13.43"><ele>37</ele></trkpt>
  <trkpt lat="52.56" lon="13.44"><ele>38</ele></trkpt>
 </trkseg></trk>
</gpx>"""


@pytest.fixture
def gpx_file(tmp_path):
    """Create a temporary GPX file."""
    path = tmp_path / "test.gpx"
    path.write_text(MINIMAL_GPX)
    return str(path)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


def test_sample_track_points(gpx_file):
    """Test GPX point sampling."""
    points = _sample_track_points(gpx_file)
    assert len(points) == 5
    assert points[0] == (52.52, 13.40)
    assert points[-1] == (52.56, 13.44)


def test_sample_track_points_sampling(tmp_path):
    """Test that large GPX files are sampled down."""
    # Generate 200 points
    pts = "\n".join(
        f'  <trkpt lat="{52.5 + i * 0.001}" lon="{13.4 + i * 0.001}"><ele>34</ele></trkpt>'
        for i in range(200)
    )
    gpx = f"""<?xml version='1.0' encoding='utf-8'?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
 <trk><trkseg>
{pts}
 </trkseg></trk>
</gpx>"""
    path = tmp_path / "big.gpx"
    path.write_text(gpx)
    points = _sample_track_points(str(path), max_points=50)
    assert len(points) <= 51  # 50 + possibly last point


def test_sample_track_points_file_not_found():
    """Test missing GPX file."""
    with pytest.raises(FileNotFoundError):
        _sample_track_points("/nonexistent/path.gpx")


def test_build_around_poly():
    """Test polyline coordinate string."""
    points = [(52.52, 13.40), (52.53, 13.41)]
    result = _build_around_poly(points)
    assert result == "52.52,13.4,52.53,13.41"


def test_build_query_single_category():
    """Test query building for a single category."""
    query = _build_query(["cafe"], "52.52,13.40,52.53,13.41", 500)
    assert "[out:json]" in query
    assert '"amenity"="cafe"' in query
    assert "around:500" in query


def test_build_query_multiple_categories():
    """Test query building for multiple categories."""
    query = _build_query(["cafe", "swimming"], "52.52,13.40", 300)
    assert '"amenity"="cafe"' in query
    assert '"leisure"="swimming_area"' in query


def test_build_query_unknown_category():
    """Test that unknown categories produce no filters."""
    query = _build_query(["nonexistent"], "52.52,13.40", 500)
    assert query == ""


def test_format_results_empty():
    """Test formatting with no results."""
    result = _format_results([], ["cafe"])
    assert "No POIs found" in result


def test_format_results_basic():
    """Test formatting with results."""
    elements = [
        {
            "type": "node",
            "lat": 52.52,
            "lon": 13.40,
            "tags": {
                "name": "Café Schön",
                "amenity": "cafe",
                "cuisine": "coffee_shop",
                "opening_hours": "Mo-Fr 08:00-18:00",
            },
        },
        {
            "type": "node",
            "lat": 52.53,
            "lon": 13.41,
            "tags": {
                "name": "Biergarten am See",
                "amenity": "biergarten",
            },
        },
    ]
    result = _format_results(elements, ["cafe", "beer_garden"])
    assert "Café Schön" in result
    assert "Biergarten am See" in result
    assert "coffee_shop" in result
    assert "2 POI(s)" in result


def test_format_results_deduplication():
    """Test that duplicate POIs are removed."""
    elements = [
        {"type": "node", "lat": 52.52, "lon": 13.40, "tags": {"name": "Dup", "amenity": "cafe"}},
        {"type": "node", "lat": 52.52, "lon": 13.40, "tags": {"name": "Dup", "amenity": "cafe"}},
    ]
    result = _format_results(elements, ["cafe"])
    assert "1 POI(s)" in result


def test_format_results_way_with_center():
    """Test formatting of way elements with center coordinates."""
    elements = [
        {
            "type": "way",
            "center": {"lat": 52.55, "lon": 13.43},
            "tags": {"name": "Strandbad", "leisure": "swimming_area"},
        },
    ]
    result = _format_results(elements, ["swimming"])
    assert "Strandbad" in result
    assert "52.55" in result


def test_category_presets_valid():
    """Test that all preset categories exist in POI_CATEGORIES."""
    for preset, cats in CATEGORY_PRESETS.items():
        for cat in cats:
            assert cat in POI_CATEGORIES, f"Preset '{preset}' references unknown category '{cat}'"


# ---------------------------------------------------------------------------
# Integration tests (mocked HTTP)
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_search_pois_along_route_basic(gpx_file):
    """Test full POI search with mocked Overpass response."""
    mock_response = {
        "elements": [
            {
                "type": "node",
                "lat": 52.53,
                "lon": 13.41,
                "tags": {"name": "Testcafé", "amenity": "cafe"},
            },
        ]
    }
    respx.post("https://overpass-api.de/api/interpreter").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await search_pois_along_route(gpx_file, categories=["cafe"])
    assert "Testcafé" in result
    assert "1 POI(s)" in result


@respx.mock
@pytest.mark.asyncio
async def test_search_pois_along_route_preset(gpx_file):
    """Test POI search with preset."""
    mock_response = {"elements": []}
    respx.post("https://overpass-api.de/api/interpreter").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await search_pois_along_route(gpx_file, preset="einkehr")
    assert "No POIs found" in result


@pytest.mark.asyncio
async def test_search_pois_missing_gpx():
    """Test error on missing GPX file."""
    result = await search_pois_along_route("/nonexistent.gpx", categories=["cafe"])
    assert "Error" in result


@pytest.mark.asyncio
async def test_search_pois_invalid_preset():
    """Test error on invalid preset."""
    result = await search_pois_along_route("/some.gpx", preset="nonexistent")
    assert "Error" in result
    assert "unknown preset" in result


@pytest.mark.asyncio
async def test_search_pois_no_categories():
    """Test error when neither categories nor preset given."""
    result = await search_pois_along_route("/some.gpx")
    assert "Error" in result


@pytest.mark.asyncio
async def test_search_pois_invalid_radius():
    """Test error on invalid radius."""
    result = await search_pois_along_route("/some.gpx", categories=["cafe"], radius=5000)
    assert "Error" in result
