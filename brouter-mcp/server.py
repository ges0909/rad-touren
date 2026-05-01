import asyncio
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urlencode

import httpx
from fastmcp import FastMCP

mcp = FastMCP("BRouter Cycling Router")

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

VALID_PROFILES = {
    "trekking",
    "fastbike",
    "trekking-ignore-cr",
    "safety",
    "shortest",
    "trekking-steep",
    "trekking-noferries",
    "trekking-nosteps",
}


@dataclass
class NoGoArea:
    lon: float
    lat: float
    radius: float = 20.0


@dataclass
class RouteRequest:
    waypoints: list[list[float]]
    profile: str = "trekking"
    format: str = "gpx"
    alternativeidx: int = 0
    nogos: list[NoGoArea] | None = None
    track_name: str | None = None


@dataclass
class RouteMetadata:
    distance_m: float
    elevation_gain_m: float
    estimated_duration: str


@dataclass
class GeocodingResult:
    name: str
    coordinates: list[float] = field(default_factory=list)  # [lon, lat]
    display_address: str = ""


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def validate_waypoints(waypoints: list[list[float]]) -> str | None:
    """Return an error string if waypoints are invalid, else None."""
    if len(waypoints) < 2:
        return "At least 2 waypoints are required."
    return None


def validate_coordinates(lon: float, lat: float) -> str | None:
    """Return an error string if coordinates are out of range, else None."""
    if not (-180 <= lon <= 180):
        return (
            f"Invalid coordinates: [{lon}, {lat}] — "
            "longitude must be between -180 and 180."
        )
    if not (-90 <= lat <= 90):
        return (
            f"Invalid coordinates: [{lon}, {lat}] — "
            "latitude must be between -90 and 90."
        )
    return None


def validate_profile(profile: str) -> str | None:
    """Return an error string if the profile is not supported, else None."""
    if profile not in VALID_PROFILES:
        valid = ", ".join(sorted(VALID_PROFILES))
        return f"Invalid profile '{profile}'. Valid profiles: {valid}"
    return None


def validate_alternativeidx(idx: int) -> str | None:
    """Return an error string if the alternative index is out of range, else None."""
    if idx < 0 or idx > 3:
        return f"Invalid alternative index {idx}. Valid range is 0 to 3."
    return None


# ---------------------------------------------------------------------------
# Route request builder
# ---------------------------------------------------------------------------

BROUTER_BASE_URL = "https://brouter.de/brouter"


def build_brouter_url(
    waypoints: list[list[float]],
    profile: str,
    format: str,
    alternativeidx: int,
    nogos: list[NoGoArea] | None = None,
) -> str:
    """Build a BRouter API URL from route parameters.

    Waypoints are formatted as ``lon,lat|lon,lat|...`` in the ``lonlats``
    query parameter.  No-go areas are included only when provided.
    """
    lonlats = "|".join(f"{lon},{lat}" for lon, lat in waypoints)

    params: dict[str, str] = {
        "lonlats": lonlats,
        "profile": profile,
        "format": format,
        "alternativeidx": str(alternativeidx),
    }

    if nogos:
        nogos_str = "|".join(
            f"{nogo.lon},{nogo.lat},{nogo.radius}" for nogo in nogos
        )
        params["nogos"] = nogos_str

    return f"{BROUTER_BASE_URL}?{urlencode(params)}"


# ---------------------------------------------------------------------------
# GPX helpers
# ---------------------------------------------------------------------------

# Patterns for metadata embedded in the GPX creator attribute or comment
_TRACK_LENGTH_RE = re.compile(r'track-length\s*=\s*"?(\d+(?:\.\d+)?)"?')
_FILTERED_ASCEND_RE = re.compile(r'filtered ascend\s*=\s*"?(\d+(?:\.\d+)?)"?')

# Average speeds per profile (km/h) for duration estimation
_PROFILE_SPEEDS: dict[str, float] = {
    "trekking": 15.0,
    "fastbike": 20.0,
}
_DEFAULT_SPEED = 12.0  # km/h for all other profiles


def parse_gpx_metadata(gpx_content: str) -> RouteMetadata:
    """Extract track-length and filtered ascend from GPX content.

    BRouter embeds metadata in the GPX ``creator`` attribute or a comment
    header, e.g.::

        track-length = "42350" filtered ascend = "312"

    Returns a :class:`RouteMetadata` with distance, elevation gain, and a
    placeholder duration (call :func:`calculate_duration` separately).
    """
    length_match = _TRACK_LENGTH_RE.search(gpx_content)
    ascend_match = _FILTERED_ASCEND_RE.search(gpx_content)

    distance_m = float(length_match.group(1)) if length_match else 0.0
    elevation_gain_m = float(ascend_match.group(1)) if ascend_match else 0.0

    return RouteMetadata(
        distance_m=distance_m,
        elevation_gain_m=elevation_gain_m,
        estimated_duration="",  # filled in by calculate_duration
    )


def calculate_duration(distance_m: float, profile: str) -> str:
    """Estimate cycling duration based on profile average speed.

    Returns a string formatted as ``"Xh Ym"``.
    """
    speed_kmh = _PROFILE_SPEEDS.get(profile, _DEFAULT_SPEED)
    distance_km = distance_m / 1000.0
    hours = distance_km / speed_kmh
    total_minutes = round(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}h {m}m"


# GPX namespace used by BRouter
_GPX_NS = "http://www.topografix.com/GPX/1/1"


def insert_track_name(gpx_content: str, name: str) -> str:
    """Insert or replace a ``<name>`` element inside the ``<trk>`` element.

    Uses :mod:`xml.etree.ElementTree` for XML manipulation.
    """
    # Register the default namespace so output doesn't get ns0: prefixes
    ET.register_namespace("", _GPX_NS)

    root = ET.fromstring(gpx_content)

    # Find <trk> — try with namespace first, then without
    trk = root.find(f"{{{_GPX_NS}}}trk")
    if trk is None:
        trk = root.find("trk")
    if trk is None:
        return gpx_content  # no <trk> element, return unchanged

    # Look for existing <name> child
    name_elem = trk.find(f"{{{_GPX_NS}}}name")
    if name_elem is None:
        name_elem = trk.find("name")

    if name_elem is None:
        # Create a new <name> element and insert at the beginning of <trk>
        name_elem = ET.SubElement(trk, "name")
        # Move it to be the first child
        trk.remove(name_elem)
        trk.insert(0, name_elem)

    name_elem.text = name

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


# ---------------------------------------------------------------------------
# Nominatim rate limiter
# ---------------------------------------------------------------------------

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "brouter-mcp/1.0 (cycling tour planner)"


class NominatimRateLimiter:
    """Async rate limiter that enforces minimum 1 second between requests."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._last_request_time: float = 0.0

    async def acquire(self) -> None:
        """Wait until at least 1 second has passed since the last request."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
            self._last_request_time = time.monotonic()


# Module-level rate limiter instance
_nominatim_rate_limiter = NominatimRateLimiter()


# ---------------------------------------------------------------------------
# HTTP client functions
# ---------------------------------------------------------------------------


async def call_brouter(url: str) -> str:
    """Send an async GET request to the BRouter API.

    Returns the response text on success, or a descriptive error string
    on failure.  Uses a 60-second timeout.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as exc:
        return (
            f"BRouter API error (HTTP {exc.response.status_code}): "
            f"{exc.response.text}"
        )
    except (httpx.TimeoutException, httpx.ConnectError):
        return "BRouter API at brouter.de is unavailable"


async def call_nominatim(params: dict) -> list[dict] | str:
    """Send an async GET request to the Nominatim search API.

    Returns a list of result dicts on success, or a descriptive error
    string on failure.  Uses a 10-second timeout and enforces rate
    limiting via :class:`NominatimRateLimiter`.
    """
    await _nominatim_rate_limiter.acquire()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_BASE_URL,
                params=params,
                headers={"User-Agent": NOMINATIM_USER_AGENT},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        return (
            f"Nominatim API error (HTTP {exc.response.status_code})"
        )
    except (httpx.TimeoutException, httpx.ConnectError):
        return "Nominatim geocoding service is unavailable"


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def calculate_route(
    waypoints: list[list[float]],
    profile: str = "trekking",
    format: str = "gpx",
    alternativeidx: int = 0,
    nogos: list[dict] | None = None,
    track_name: str | None = None,
) -> str:
    """Calculate a cycling route through waypoints via the BRouter API.

    Args:
        waypoints: List of [longitude, latitude] coordinate pairs (minimum 2).
        profile: Cycling profile name (default: "trekking"). Valid profiles:
            trekking, fastbike, trekking-ignore-cr, safety, shortest,
            trekking-steep, trekking-noferries, trekking-nosteps.
        format: Output format — "gpx" (default) or "geojson".
        alternativeidx: Alternative route index 0–3 (default: 0).
        nogos: Optional list of no-go areas, each a dict with keys
            "lon", "lat", and optional "radius" (meters, default 20).
        track_name: Optional name to insert into the GPX <trk><name> element.

    Returns:
        Route summary with GPX/GeoJSON data, or a descriptive error message.
    """
    # --- Input validation ---
    err = validate_waypoints(waypoints)
    if err:
        return err

    for wp in waypoints:
        if len(wp) < 2:
            return f"Invalid waypoint {wp}: each waypoint must be [longitude, latitude]."
        err = validate_coordinates(wp[0], wp[1])
        if err:
            return err

    err = validate_profile(profile)
    if err:
        return err

    err = validate_alternativeidx(alternativeidx)
    if err:
        return err

    # --- Convert no-go dicts to NoGoArea dataclasses ---
    nogo_areas: list[NoGoArea] | None = None
    if nogos:
        nogo_areas = []
        for nogo in nogos:
            lon = nogo.get("lon", 0.0)
            lat = nogo.get("lat", 0.0)
            radius = nogo.get("radius", 20.0)
            err = validate_coordinates(lon, lat)
            if err:
                return f"Invalid no-go area coordinates: {err}"
            nogo_areas.append(NoGoArea(lon=lon, lat=lat, radius=radius))

    # --- Build URL and call BRouter ---
    url = build_brouter_url(waypoints, profile, format, alternativeidx, nogo_areas)
    result = await call_brouter(url)

    # Check for error responses from call_brouter
    if result.startswith("BRouter API"):
        return result

    # --- Handle GeoJSON response ---
    if format == "geojson":
        return f"## Route (GeoJSON)\n\n```json\n{result}\n```"

    # --- Handle GPX response ---
    # Verify the GPX contains a <trk> element
    if "<trk>" not in result and f"<trk " not in result and f"{{{_GPX_NS}}}trk" not in result:
        return "Error: BRouter returned an invalid GPX response (missing <trk> element)."

    # Extract metadata
    metadata = parse_gpx_metadata(result)
    metadata.estimated_duration = calculate_duration(metadata.distance_m, profile)

    # Optionally insert track name
    gpx_content = result
    if track_name:
        gpx_content = insert_track_name(gpx_content, track_name)

    # Format distance for display
    distance_km = metadata.distance_m / 1000.0

    return (
        f"## Route Summary\n"
        f"- Distance: {distance_km:.1f} km\n"
        f"- Elevation gain: {metadata.elevation_gain_m:.0f} m\n"
        f"- Estimated duration: {metadata.estimated_duration}\n"
        f"- Profile: {profile}\n"
        f"- Format: gpx\n"
        f"\n"
        f"## GPX Data\n"
        f"{gpx_content}"
    )


def transform_nominatim_result(item: dict) -> GeocodingResult:
    """Transform a single Nominatim JSON result into a GeocodingResult.

    Converts Nominatim's ``lat``/``lon`` string fields to a
    ``[longitude, latitude]`` coordinate pair (longitude-first).
    """
    return GeocodingResult(
        name=item.get("name", item.get("display_name", "")),
        coordinates=[float(item["lon"]), float(item["lat"])],
        display_address=item.get("display_name", ""),
    )


@mcp.tool()
async def search_location(
    query: str,
    country_code: str = "de",
    limit: int = 5,
) -> str:
    """Search for locations by name via the Nominatim geocoding API.

    Args:
        query: Search query string (place name, address, etc.).
        country_code: ISO 3166-1 alpha-2 country code to restrict results
            (default: "de" for Germany).
        limit: Maximum number of results to return, 1–40 (default: 5).

    Returns:
        Structured text with numbered search results including coordinates
        as [longitude, latitude], or a descriptive error/no-results message.
    """
    params = {
        "q": query,
        "format": "jsonv2",
        "countrycodes": country_code,
        "limit": str(limit),
    }

    result = await call_nominatim(params)

    # call_nominatim returns a string on error
    if isinstance(result, str):
        return result

    if not result:
        return (
            f'No locations found for "{query}". '
            "Try a different search term or check the spelling."
        )

    geocoding_results = [transform_nominatim_result(item) for item in result]

    lines = [f'## Search Results for "{query}"\n']
    for i, gr in enumerate(geocoding_results, start=1):
        lines.append(
            f"{i}. {gr.name}\n"
            f"   Coordinates: [{gr.coordinates[0]}, {gr.coordinates[1]}]\n"
            f"   Address: {gr.display_address}\n"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
