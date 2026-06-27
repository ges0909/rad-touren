"""Property-based and unit tests for the BRouter MCP server."""

from urllib.parse import parse_qs, urlparse

from hypothesis import assume, given, settings
from hypothesis import strategies as st
from server import (
    _DEFAULT_SPEED,
    _GPX_NS,
    _PROFILE_SPEEDS,
    BROUTER_BASE_URL,
    NOMINATIM_BASE_URL,
    VALID_PROFILES,
    NoGoArea,
    build_brouter_url,
    calculate_duration,
    insert_track_name,
    parse_gpx_metadata,
    transform_nominatim_result,
    validate_coordinates,
    validate_profile,
)

# ---------------------------------------------------------------------------
# Property 3: Coordinate validation accepts valid ranges and rejects invalid
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    lon=st.floats(allow_nan=False, allow_infinity=False),
    lat=st.floats(allow_nan=False, allow_infinity=False),
)
def test_coordinate_validation_accepts_valid_rejects_invalid(lon: float, lat: float) -> None:
    """validate_coordinates accepts (lon, lat) iff lon ∈ [-180, 180] and lat ∈ [-90, 90]."""
    result = validate_coordinates(lon, lat)
    lon_ok = -180 <= lon <= 180
    lat_ok = -90 <= lat <= 90

    if lon_ok and lat_ok:
        assert result is None, (
            f"Expected acceptance for valid coordinates [{lon}, {lat}], got: {result}"
        )
    else:
        assert result is not None, f"Expected rejection for invalid coordinates [{lon}, {lat}]"
        # Error message should mention the offending coordinates
        assert str(lon) in result or str(lat) in result


# ---------------------------------------------------------------------------
# Property 2: Profile validation accepts exactly the valid set
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(profile=st.sampled_from(sorted(VALID_PROFILES)))
def test_profile_validation_accepts_valid_profiles(profile: str) -> None:
    """validate_profile accepts every profile in the valid set."""
    result = validate_profile(profile)
    assert result is None, f"Expected acceptance for valid profile '{profile}', got: {result}"


@settings(max_examples=100)
@given(profile=st.text(min_size=0, max_size=50))
def test_profile_validation_rejects_invalid_profiles(profile: str) -> None:
    """validate_profile rejects any string not in the valid set."""
    assume(profile not in VALID_PROFILES)
    result = validate_profile(profile)
    assert result is not None, f"Expected rejection for invalid profile '{profile}'"
    # Error message should list valid options
    for valid in VALID_PROFILES:
        assert valid in result, f"Error message should list valid profile '{valid}', got: {result}"


# ---------------------------------------------------------------------------
# Hypothesis strategies for route parameters
# ---------------------------------------------------------------------------

# Coordinate pair: [lon, lat] within valid ranges
_coordinate_st = st.tuples(
    st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False),
).map(list)

# List of 2+ waypoints
_waypoints_st = st.lists(_coordinate_st, min_size=2, max_size=10)

_profile_st = st.sampled_from(sorted(VALID_PROFILES))
_format_st = st.sampled_from(["gpx", "geojson"])
_altidx_st = st.integers(min_value=0, max_value=3)

_nogo_st = st.builds(
    NoGoArea,
    lon=st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False),
    lat=st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False),
    radius=st.floats(min_value=0.1, max_value=10000, allow_nan=False, allow_infinity=False),
)

_nogos_st = st.one_of(
    st.none(),
    st.lists(_nogo_st, min_size=1, max_size=5),
)


# ---------------------------------------------------------------------------
# Property 1: URL construction preserves all route parameters
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    waypoints=_waypoints_st,
    profile=_profile_st,
    fmt=_format_st,
    alternativeidx=_altidx_st,
    nogos=_nogos_st,
)
def test_url_construction_preserves_all_route_parameters(
    waypoints: list[list[float]],
    profile: str,
    fmt: str,
    alternativeidx: int,
    nogos: list[NoGoArea] | None,
) -> None:
    """build_brouter_url produces a URL containing all supplied parameters."""
    url = build_brouter_url(waypoints, profile, fmt, alternativeidx, nogos)

    # URL starts with the correct base
    assert url.startswith(BROUTER_BASE_URL), f"URL should start with {BROUTER_BASE_URL}, got: {url}"

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # (a) lonlats parameter contains all waypoints in lon,lat order
    assert "lonlats" in params, "URL must contain 'lonlats' parameter"
    lonlats_value = params["lonlats"][0]
    lonlat_pairs = lonlats_value.split("|")
    assert len(lonlat_pairs) == len(waypoints), (
        f"Expected {len(waypoints)} waypoint pairs, got {len(lonlat_pairs)}"
    )
    for i, (pair_str, wp) in enumerate(zip(lonlat_pairs, waypoints)):
        parts = pair_str.split(",")
        assert len(parts) == 2, f"Waypoint {i} should have 2 components, got: {pair_str}"
        parsed_lon, parsed_lat = float(parts[0]), float(parts[1])
        assert parsed_lon == wp[0], (
            f"Waypoint {i} longitude mismatch: expected {wp[0]}, got {parsed_lon}"
        )
        assert parsed_lat == wp[1], (
            f"Waypoint {i} latitude mismatch: expected {wp[1]}, got {parsed_lat}"
        )

    # (b) profile parameter matches
    assert params["profile"] == [profile], (
        f"Expected profile '{profile}', got {params.get('profile')}"
    )

    # (c) format parameter matches
    assert params["format"] == [fmt], f"Expected format '{fmt}', got {params.get('format')}"

    # (d) alternativeidx parameter matches
    assert params["alternativeidx"] == [str(alternativeidx)], (
        f"Expected alternativeidx '{alternativeidx}', got {params.get('alternativeidx')}"
    )

    # (e) nogos parameter present iff no-go areas provided
    if nogos:
        assert "nogos" in params, "URL must contain 'nogos' when no-go areas provided"
        nogos_value = params["nogos"][0]
        nogo_parts = nogos_value.split("|")
        assert len(nogo_parts) == len(nogos), (
            f"Expected {len(nogos)} no-go areas, got {len(nogo_parts)}"
        )
        for j, (nogo_str, nogo) in enumerate(zip(nogo_parts, nogos)):
            components = nogo_str.split(",")
            assert len(components) == 3, (
                f"No-go area {j} should have 3 components (lon,lat,radius), got: {nogo_str}"
            )
            assert float(components[0]) == nogo.lon, (
                f"No-go {j} lon mismatch: expected {nogo.lon}, got {components[0]}"
            )
            assert float(components[1]) == nogo.lat, (
                f"No-go {j} lat mismatch: expected {nogo.lat}, got {components[1]}"
            )
            assert float(components[2]) == nogo.radius, (
                f"No-go {j} radius mismatch: expected {nogo.radius}, got {components[2]}"
            )
    else:
        assert "nogos" not in params, "URL should not contain 'nogos' when no no-go areas provided"


# ---------------------------------------------------------------------------
# Property 5: GPX metadata extraction round-trip
# ---------------------------------------------------------------------------

# Strategy for non-negative numeric values that BRouter embeds as integers
# or decimals in the GPX header.  We use integers here because BRouter
# typically writes whole-number strings for track-length and filtered ascend.
_gpx_metric_int_st = st.integers(min_value=0, max_value=10_000_000)
_gpx_metric_float_st = st.floats(
    min_value=0,
    max_value=10_000_000,
    allow_nan=False,
    allow_infinity=False,
)


def _make_gpx_with_metadata(track_length: str, filtered_ascend: str) -> str:
    """Build a minimal GPX string with BRouter-style metadata.

    BRouter embeds metadata in the ``creator`` attribute of the ``<gpx>``
    element.  When the raw HTTP response is received (before any XML
    parsing), the attribute value contains literal quote characters around
    the metric values, e.g.::

        creator="BRouter-1.7.0 track-length = "42350" filtered ascend = "312""

    We replicate this by placing the metadata in an XML comment, which
    preserves literal quotes and matches what ``parse_gpx_metadata`` sees
    when scanning the raw response text.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- BRouter-1.7.0 track-length = "{track_length}" '
        f'filtered ascend = "{filtered_ascend}" -->\n'
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n'
        "  <trk><trkseg>"
        '    <trkpt lat="52.0" lon="13.0"><ele>50</ele></trkpt>'
        "  </trkseg></trk>\n"
        "</gpx>"
    )


@settings(max_examples=100)
@given(
    track_length=_gpx_metric_int_st,
    filtered_ascend=_gpx_metric_int_st,
)
def test_gpx_metadata_extraction_roundtrip_integers(
    track_length: int, filtered_ascend: int
) -> None:
    """parse_gpx_metadata extracts integer track-length and filtered ascend correctly."""
    gpx = _make_gpx_with_metadata(str(track_length), str(filtered_ascend))
    meta = parse_gpx_metadata(gpx)

    assert meta.distance_m == float(track_length), (
        f"Expected distance_m={float(track_length)}, got {meta.distance_m}"
    )
    assert meta.elevation_gain_m == float(filtered_ascend), (
        f"Expected elevation_gain_m={float(filtered_ascend)}, got {meta.elevation_gain_m}"
    )


@settings(max_examples=100)
@given(
    track_length=_gpx_metric_float_st,
    filtered_ascend=_gpx_metric_float_st,
)
def test_gpx_metadata_extraction_roundtrip_floats(
    track_length: float, filtered_ascend: float
) -> None:
    """parse_gpx_metadata extracts decimal track-length and filtered ascend correctly."""
    # Format with enough precision to survive the round-trip through str → regex → float.
    # We compare against the re-parsed string value to account for formatting precision.
    tl_str = f"{track_length:.6f}"
    fa_str = f"{filtered_ascend:.6f}"

    gpx = _make_gpx_with_metadata(tl_str, fa_str)
    meta = parse_gpx_metadata(gpx)

    expected_distance = float(tl_str)
    expected_ascend = float(fa_str)

    assert meta.distance_m == expected_distance, (
        f"Expected distance_m={expected_distance}, got {meta.distance_m}"
    )
    assert meta.elevation_gain_m == expected_ascend, (
        f"Expected elevation_gain_m={expected_ascend}, got {meta.elevation_gain_m}"
    )


# ---------------------------------------------------------------------------
# Property 5b: GPX metadata extraction — unquoted format (real BRouter 1.7.9)
# ---------------------------------------------------------------------------


def _make_gpx_with_unquoted_metadata(track_length: str, filtered_ascend: str) -> str:
    """Build a GPX string with BRouter 1.7.9 unquoted metadata format.

    BRouter 1.7.9 writes metadata values *without* quotes in the XML
    comment, e.g.::

        <!-- track-length = 42350 filtered ascend = 312 plain-ascend = 287 ... -->

    This helper replicates that format to ensure the regex handles both
    quoted and unquoted values.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<!-- track-length = {track_length} "
        f"filtered ascend = {filtered_ascend} "
        f"plain-ascend = 0 cost=0 -->\n"
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n'
        "  <trk><trkseg>"
        '    <trkpt lat="52.0" lon="13.0"><ele>50</ele></trkpt>'
        "  </trkseg></trk>\n"
        "</gpx>"
    )


@settings(max_examples=100)
@given(
    track_length=_gpx_metric_int_st,
    filtered_ascend=_gpx_metric_int_st,
)
def test_gpx_metadata_extraction_unquoted_format(track_length: int, filtered_ascend: int) -> None:
    """parse_gpx_metadata handles BRouter 1.7.9 unquoted metadata values."""
    gpx = _make_gpx_with_unquoted_metadata(str(track_length), str(filtered_ascend))
    meta = parse_gpx_metadata(gpx)

    assert meta.distance_m == float(track_length), (
        f"Expected distance_m={float(track_length)}, got {meta.distance_m}"
    )
    assert meta.elevation_gain_m == float(filtered_ascend), (
        f"Expected elevation_gain_m={float(filtered_ascend)}, got {meta.elevation_gain_m}"
    )


# ---------------------------------------------------------------------------
# Property 6: Duration calculation correctness
# ---------------------------------------------------------------------------


@settings(max_examples=100)
@given(
    distance_m=st.floats(min_value=0.1, max_value=1_000_000, allow_nan=False, allow_infinity=False),
    profile=st.sampled_from(sorted(VALID_PROFILES)),
)
def test_duration_calculation_correctness(distance_m: float, profile: str) -> None:
    """calculate_duration returns distance/speed formatted as 'Xh Ym' with correct speed per profile."""
    result = calculate_duration(distance_m, profile)

    # Determine expected speed
    speed_kmh = _PROFILE_SPEEDS.get(profile, _DEFAULT_SPEED)

    # Replicate the formula from the implementation
    distance_km = distance_m / 1000.0
    hours = distance_km / speed_kmh
    total_minutes = round(hours * 60)
    expected_h = total_minutes // 60
    expected_m = total_minutes % 60
    expected = f"{expected_h}h {expected_m}m"

    assert result == expected, (
        f"For distance={distance_m}m, profile='{profile}' (speed={speed_kmh} km/h): "
        f"expected '{expected}', got '{result}'"
    )

    # Verify format is always "Xh Ym"
    import re

    assert re.fullmatch(r"\d+h \d+m", result), (
        f"Duration should match 'Xh Ym' format, got: '{result}'"
    )


# ---------------------------------------------------------------------------
# Property 4: Track name insertion into GPX
# ---------------------------------------------------------------------------

import xml.etree.ElementTree as ET

# Strategy for non-empty track names.  We restrict to characters that are
# valid in XML 1.0 text content and survive an ElementTree round-trip.
# XML 1.0 allows: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | ...
# However, \r is normalised to \n by the XML parser (per the XML spec),
# so we exclude it to keep the property assertion straightforward.
_track_name_st = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",),  # exclude surrogates
        whitelist_characters="\t\n",
        blacklist_characters=(
            "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\r"
            "\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19"
            "\x1a\x1b\x1c\x1d\x1e\x1f"
            "\ufffe\uffff"
        ),
    ),
    min_size=1,
    max_size=200,
)


def _make_gpx_with_trk(extra_children: str = "") -> str:
    """Build a minimal valid GPX string with a ``<trk>`` element."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <trk>{extra_children}<trkseg>"
        '    <trkpt lat="52.0" lon="13.0"><ele>50</ele></trkpt>'
        "  </trkseg></trk>\n"
        "</gpx>"
    )


@settings(max_examples=100)
@given(name=_track_name_st)
def test_track_name_insertion_into_gpx(name: str) -> None:
    """insert_track_name produces GPX where <trk> has a <name> child with the given text."""
    gpx_input = _make_gpx_with_trk()
    result = insert_track_name(gpx_input, name)

    # Parse the result and find the <trk> element
    root = ET.fromstring(result)
    trk = root.find(f"{{{_GPX_NS}}}trk")
    if trk is None:
        trk = root.find("trk")
    assert trk is not None, "Result GPX must contain a <trk> element"

    # Find the <name> child
    name_elem = trk.find(f"{{{_GPX_NS}}}name")
    if name_elem is None:
        name_elem = trk.find("name")
    assert name_elem is not None, "Result GPX <trk> must contain a <name> child element"
    assert name_elem.text == name, f"Expected <name> text to be {name!r}, got {name_elem.text!r}"


@settings(max_examples=100)
@given(name=_track_name_st)
def test_track_name_insertion_replaces_existing_name(name: str) -> None:
    """insert_track_name replaces an existing <name> element rather than adding a duplicate."""
    # Start with a GPX that already has a <name> inside <trk>
    ns = "http://www.topografix.com/GPX/1/1"
    gpx_input = _make_gpx_with_trk(f'<name xmlns="{ns}">Old Name</name>')
    result = insert_track_name(gpx_input, name)

    root = ET.fromstring(result)
    trk = root.find(f"{{{_GPX_NS}}}trk")
    if trk is None:
        trk = root.find("trk")
    assert trk is not None

    # There should be exactly one <name> element (replaced, not duplicated)
    name_elems = trk.findall(f"{{{_GPX_NS}}}name") + trk.findall("name")
    assert len(name_elems) == 1, f"Expected exactly 1 <name> element, found {len(name_elems)}"
    assert name_elems[0].text == name, (
        f"Expected <name> text to be {name!r}, got {name_elems[0].text!r}"
    )


# ---------------------------------------------------------------------------
# Unit tests: calculate_route edge cases (Task 6.2)
# ---------------------------------------------------------------------------

import asyncio

import httpx
import respx
from server import calculate_route


def _make_brouter_gpx(
    track_length: int = 42350,
    filtered_ascend: int = 312,
    track_name: str | None = None,
) -> str:
    """Build a realistic BRouter GPX response string."""
    name_elem = f"<name>{track_name}</name>" if track_name else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<gpx version="1.1" creator="BRouter-1.7.0" '
        f'xmlns="http://www.topografix.com/GPX/1/1">\n'
        f'<!-- track-length = "{track_length}" '
        f'filtered ascend = "{filtered_ascend}" -->\n'
        f"  <trk>{name_elem}<trkseg>"
        '    <trkpt lat="52.5" lon="13.4"><ele>34</ele></trkpt>'
        '    <trkpt lat="52.6" lon="13.5"><ele>45</ele></trkpt>'
        "  </trkseg></trk>\n"
        "</gpx>"
    )


@respx.mock
def test_calculate_route_default_profile_is_trekking() -> None:
    """When no profile is specified, the BRouter request uses 'trekking'."""
    gpx = _make_brouter_gpx()
    route = respx.get(BROUTER_BASE_URL).mock(return_value=httpx.Response(200, text=gpx))

    result = asyncio.run(
        calculate_route(
            waypoints=[[13.4, 52.5], [13.5, 52.6]],
        )
    )

    assert route.called
    request_url = str(route.calls[0].request.url)
    assert "profile=trekking" in request_url
    assert "- Profile: trekking" in result


@respx.mock
def test_calculate_route_default_format_is_gpx() -> None:
    """When no format is specified, the BRouter request uses 'gpx'."""
    gpx = _make_brouter_gpx()
    route = respx.get(BROUTER_BASE_URL).mock(return_value=httpx.Response(200, text=gpx))

    result = asyncio.run(
        calculate_route(
            waypoints=[[13.4, 52.5], [13.5, 52.6]],
        )
    )

    assert route.called
    request_url = str(route.calls[0].request.url)
    assert "format=gpx" in request_url
    assert "- Format: gpx" in result


@respx.mock
def test_calculate_route_default_alternativeidx_is_zero() -> None:
    """When no alternativeidx is specified, the BRouter request uses '0'."""
    gpx = _make_brouter_gpx()
    route = respx.get(BROUTER_BASE_URL).mock(return_value=httpx.Response(200, text=gpx))

    result = asyncio.run(
        calculate_route(
            waypoints=[[13.4, 52.5], [13.5, 52.6]],
        )
    )

    assert route.called
    request_url = str(route.calls[0].request.url)
    assert "alternativeidx=0" in request_url


@respx.mock
def test_calculate_route_round_trip_includes_all_waypoints() -> None:
    """A round-trip route (identical start/end) includes all intermediate waypoints."""
    gpx = _make_brouter_gpx()
    route = respx.get(BROUTER_BASE_URL).mock(return_value=httpx.Response(200, text=gpx))

    # Start and end are the same; two intermediate waypoints define the loop
    waypoints = [
        [13.4, 52.5],  # start
        [13.5, 52.6],  # intermediate 1
        [13.6, 52.55],  # intermediate 2
        [13.4, 52.5],  # end == start
    ]
    asyncio.run(calculate_route(waypoints=waypoints))

    assert route.called
    request_url = str(route.calls[0].request.url)
    # All four waypoints must appear in the lonlats parameter
    assert "13.4%2C52.5" in request_url or "13.4,52.5" in request_url
    assert "13.5%2C52.6" in request_url or "13.5,52.6" in request_url
    assert "13.6%2C52.55" in request_url or "13.6,52.55" in request_url

    # Verify the lonlats value has exactly 4 pipe-separated pairs
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(request_url)
    params = parse_qs(parsed.query)
    lonlat_pairs = params["lonlats"][0].split("|")
    assert len(lonlat_pairs) == 4, (
        f"Expected 4 waypoint pairs for round-trip, got {len(lonlat_pairs)}"
    )


@respx.mock
def test_calculate_route_no_nogos_omitted_from_url() -> None:
    """When no no-go areas are provided, the 'nogos' parameter is absent from the URL."""
    gpx = _make_brouter_gpx()
    route = respx.get(BROUTER_BASE_URL).mock(return_value=httpx.Response(200, text=gpx))

    asyncio.run(
        calculate_route(
            waypoints=[[13.4, 52.5], [13.5, 52.6]],
        )
    )

    assert route.called
    request_url = str(route.calls[0].request.url)
    assert "nogos" not in request_url


def test_calculate_route_missing_trk_returns_error() -> None:
    """GPX response without a <trk> element returns an error message."""
    # A GPX response that has no <trk> element at all
    bad_gpx = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n'
        '  <wpt lat="52.5" lon="13.4"><name>Test</name></wpt>\n'
        "</gpx>"
    )

    with respx.mock:
        respx.get(BROUTER_BASE_URL).mock(return_value=httpx.Response(200, text=bad_gpx))

        result = asyncio.run(
            calculate_route(
                waypoints=[[13.4, 52.5], [13.5, 52.6]],
            )
        )

    assert "invalid GPX response" in result.lower() or "missing <trk>" in result.lower(), (
        f"Expected error about missing <trk>, got: {result}"
    )


# ---------------------------------------------------------------------------
# Property 7: Nominatim result transformation preserves coordinates as
#              longitude-first
# ---------------------------------------------------------------------------

from server import search_location

# Strategy for Nominatim-like response dicts
_nominatim_name_st = st.text(min_size=1, max_size=100)
_nominatim_lon_st = st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False)
_nominatim_lat_st = st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False)
_nominatim_display_name_st = st.text(min_size=1, max_size=300)


@settings(max_examples=100)
@given(
    name=_nominatim_name_st,
    lon=_nominatim_lon_st,
    lat=_nominatim_lat_st,
    display_name=_nominatim_display_name_st,
)
def test_nominatim_result_transformation_preserves_lon_first(
    name: str, lon: float, lat: float, display_name: str
) -> None:
    """transform_nominatim_result produces [lon, lat] coordinates and maps fields correctly."""
    item = {
        "name": name,
        "lon": str(lon),
        "lat": str(lat),
        "display_name": display_name,
    }

    result = transform_nominatim_result(item)

    # Coordinates must be [longitude, latitude] — longitude first
    assert result.coordinates == [lon, lat], (
        f"Expected coordinates [{lon}, {lat}], got {result.coordinates}"
    )
    # Name must match
    assert result.name == name, f"Expected name {name!r}, got {result.name!r}"
    # Display address must match display_name
    assert result.display_address == display_name, (
        f"Expected display_address {display_name!r}, got {result.display_address!r}"
    )


# ---------------------------------------------------------------------------
# Unit tests: search_location edge cases (Task 7.3)
# ---------------------------------------------------------------------------


@respx.mock
def test_search_location_default_country_code_is_de() -> None:
    """When no country_code is specified, the Nominatim request uses 'de'."""
    nominatim_route = respx.get(NOMINATIM_BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "name": "Berlin Hauptbahnhof",
                    "lon": "13.3694",
                    "lat": "52.5251",
                    "display_name": "Berlin Hauptbahnhof, Berlin, Deutschland",
                }
            ],
        )
    )

    result = asyncio.run(search_location(query="Berlin Hauptbahnhof"))

    assert nominatim_route.called
    request_url = str(nominatim_route.calls[0].request.url)
    assert "countrycodes=de" in request_url


@respx.mock
def test_search_location_empty_results_returns_no_locations_message() -> None:
    """When Nominatim returns zero results, the tool returns a 'no locations found' message."""
    respx.get(NOMINATIM_BASE_URL).mock(return_value=httpx.Response(200, json=[]))

    result = asyncio.run(search_location(query="xyznonexistentplace"))

    assert "no locations found" in result.lower()
    assert "xyznonexistentplace" in result
