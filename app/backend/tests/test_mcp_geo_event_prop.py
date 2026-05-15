"""Property test: Geo-Event Emission.

**Validates: Requirements 9.1, 9.2, 9.3**

For any tool response from a geo-relevant tool (name matching route/geocode/
search_location patterns) that contains geometry or coordinate data, the agent
loop SHALL emit a `map` SSE event with coordinates in `[[lat, lng], ...]` format.

Since testing the full agent loop requires too much mocking, this test validates
the helper functions `_is_route_tool` and `_is_geocode_tool` that drive geo-event
emission decisions.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from agent import GEO_POINT_PATTERNS, GEO_ROUTE_PATTERNS, _is_geocode_tool, _is_route_tool


# --- Strategies ---

# Random prefix: simulates mcp_<server>_ style prefixes
prefix_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,20}", fullmatch=True)

# Random suffix: simulates additional tool name parts
suffix_strategy = st.from_regex(r"[a-z0-9_]{0,15}", fullmatch=True)

# Non-geo tool names: names that do NOT contain any geo patterns
NON_GEO_PATTERNS = list(GEO_ROUTE_PATTERNS) + list(GEO_POINT_PATTERNS)


def _contains_geo_pattern(name: str) -> bool:
    """Check if a name contains any geo pattern substring."""
    return any(p in name for p in NON_GEO_PATTERNS)


# Strategy for names guaranteed to NOT contain geo patterns
non_geo_name_strategy = st.from_regex(
    r"[a-z][a-z0-9_]{0,20}", fullmatch=True
).filter(lambda n: not _contains_geo_pattern(n))


# --- Property Tests ---


@given(prefix=prefix_strategy, suffix=suffix_strategy)
@settings(max_examples=100, deadline=None)
def test_route_tool_detection_with_route_pattern(prefix: str, suffix: str) -> None:
    """Route tool detection: names containing 'route' are detected.

    **Validates: Requirements 9.1, 9.3**

    For any tool name with 'route' embedded (with arbitrary prefix/suffix),
    _is_route_tool SHALL return True.
    """
    name = f"{prefix}_route_{suffix}" if suffix else f"{prefix}_route"
    assert _is_route_tool(name), f"Expected _is_route_tool('{name}') to be True"


@given(prefix=prefix_strategy, suffix=suffix_strategy)
@settings(max_examples=100, deadline=None)
def test_route_tool_detection_with_calculate_car_pattern(prefix: str, suffix: str) -> None:
    """Route tool detection: names containing 'calculate_car' are detected.

    **Validates: Requirements 9.1, 9.3**

    For any tool name with 'calculate_car' embedded (with arbitrary prefix/suffix),
    _is_route_tool SHALL return True.
    """
    name = f"{prefix}_calculate_car_{suffix}" if suffix else f"{prefix}_calculate_car"
    assert _is_route_tool(name), f"Expected _is_route_tool('{name}') to be True"


@given(prefix=prefix_strategy, suffix=suffix_strategy)
@settings(max_examples=100, deadline=None)
def test_route_tool_detection_with_calculate_bike_pattern(prefix: str, suffix: str) -> None:
    """Route tool detection: names containing 'calculate_bike' are detected.

    **Validates: Requirements 9.1, 9.3**

    For any tool name with 'calculate_bike' embedded (with arbitrary prefix/suffix),
    _is_route_tool SHALL return True.
    """
    name = f"{prefix}_calculate_bike_{suffix}" if suffix else f"{prefix}_calculate_bike"
    assert _is_route_tool(name), f"Expected _is_route_tool('{name}') to be True"


@given(prefix=prefix_strategy, suffix=suffix_strategy)
@settings(max_examples=100, deadline=None)
def test_geocode_tool_detection_with_geocode_pattern(prefix: str, suffix: str) -> None:
    """Geocode tool detection: names containing 'geocode' are detected.

    **Validates: Requirements 9.2, 9.3**

    For any tool name with 'geocode' embedded (with arbitrary prefix/suffix),
    _is_geocode_tool SHALL return True.
    """
    name = f"{prefix}_geocode_{suffix}" if suffix else f"{prefix}_geocode"
    assert _is_geocode_tool(name), f"Expected _is_geocode_tool('{name}') to be True"


@given(prefix=prefix_strategy, suffix=suffix_strategy)
@settings(max_examples=100, deadline=None)
def test_geocode_tool_detection_with_search_location_pattern(prefix: str, suffix: str) -> None:
    """Geocode tool detection: names containing 'search_location' are detected.

    **Validates: Requirements 9.2, 9.3**

    For any tool name with 'search_location' embedded (with arbitrary prefix/suffix),
    _is_geocode_tool SHALL return True.
    """
    name = f"{prefix}_search_location_{suffix}" if suffix else f"{prefix}_search_location"
    assert _is_geocode_tool(name), f"Expected _is_geocode_tool('{name}') to be True"


@given(name=non_geo_name_strategy)
@settings(max_examples=100, deadline=None)
def test_non_geo_tools_not_detected(name: str) -> None:
    """Non-geo tools: names without geo patterns return False for both functions.

    **Validates: Requirements 9.3**

    For any tool name NOT containing route/geocode/search_location patterns,
    both _is_route_tool and _is_geocode_tool SHALL return False.
    """
    assert not _is_route_tool(name), f"Expected _is_route_tool('{name}') to be False"
    assert not _is_geocode_tool(name), f"Expected _is_geocode_tool('{name}') to be False"


# --- Concrete examples for MCP-prefixed names ---


@pytest.mark.parametrize(
    "tool_name",
    [
        "mcp_brouter_calculate_route",
        "mcp_osrm_calculate_car_route",
        "mcp_osrm_route_to_gpx",
        "mcp_openrouteservice_calculate_route",
    ],
)
def test_mcp_route_tools_detected(tool_name: str) -> None:
    """MCP prefixed route tools are correctly detected.

    **Validates: Requirements 9.1, 9.3**
    """
    assert _is_route_tool(tool_name), f"Expected _is_route_tool('{tool_name}') to be True"


@pytest.mark.parametrize(
    "tool_name",
    [
        "mcp_openrouteservice_geocode",
        "mcp_brouter_search_location",
    ],
)
def test_mcp_geocode_tools_detected(tool_name: str) -> None:
    """MCP prefixed geocode tools are correctly detected.

    **Validates: Requirements 9.2, 9.3**
    """
    assert _is_geocode_tool(tool_name), f"Expected _is_geocode_tool('{tool_name}') to be True"


@pytest.mark.parametrize(
    "tool_name",
    [
        "mcp_open_meteo_weather_forecast",
        "mcp_vbb_get_departures",
        "mcp_wikivoyage_get_article",
        "mcp_overpass_search_pois_along_route",  # contains "route" → detected as route tool
    ],
)
def test_mcp_non_geo_tools_classification(tool_name: str) -> None:
    """MCP prefixed non-geo tools are classified correctly.

    **Validates: Requirements 9.3**

    Note: mcp_overpass_search_pois_along_route contains 'route' so it IS
    detected as a route tool. This is by design — the pattern matching is
    intentionally broad.
    """
    if "route" in tool_name or "calculate_car" in tool_name or "calculate_bike" in tool_name:
        assert _is_route_tool(tool_name)
    else:
        assert not _is_route_tool(tool_name)

    if "geocode" in tool_name or "search_location" in tool_name:
        assert _is_geocode_tool(tool_name)
    else:
        assert not _is_geocode_tool(tool_name)
