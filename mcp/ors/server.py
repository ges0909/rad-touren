"""MCP server wrapping OpenRouteService for car, bike, and foot routing.

Uses lib.geocoding for geocode. Routing, isochrone, and matrix use ORS directly
(not yet in shared lib due to multi-profile POST API differences).
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from lib.geocoding import geocode as _geocode

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

mcp = FastMCP("OpenRouteService Routing")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("ORS_API_KEY", "")
BASE_URL = "https://api.openrouteservice.org"

VALID_PROFILES = {
    "driving-car",
    "driving-hgv",
    "cycling-regular",
    "cycling-road",
    "cycling-mountain",
    "foot-walking",
    "foot-hiking",
}


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


async def _api_post(path: str, body: dict) -> dict | str:
    """Make authenticated POST request to ORS API."""
    if not API_KEY:
        return "Error: ORS_API_KEY environment variable not set."

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{BASE_URL}{path}",
                json=body,
                headers={
                    "Authorization": API_KEY,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return f"ORS API error {e.response.status_code}: {e.response.text[:300]}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def calculate_route(
    coordinates: list[list[float]],
    profile: str = "driving-car",
) -> str:
    """Calculate a route between waypoints with distance and duration.

    Args:
        coordinates: List of [longitude, latitude] pairs (minimum 2, maximum 50).
        profile: Routing profile. Options: driving-car, driving-hgv,
                 cycling-regular, cycling-road, cycling-mountain,
                 foot-walking, foot-hiking. Default: driving-car.

    Returns:
        Route summary with total distance, duration, and per-segment breakdown.
    """
    if not coordinates or len(coordinates) < 2:
        return "Error: at least 2 coordinate pairs required"
    if len(coordinates) > 50:
        return "Error: maximum 50 waypoints"
    if profile not in VALID_PROFILES:
        return f"Error: invalid profile '{profile}'. Valid: {', '.join(sorted(VALID_PROFILES))}"

    body = {
        "coordinates": coordinates,
        "instructions": False,
        "units": "km",
    }

    data = await _api_post(f"/v2/directions/{profile}/json", body)
    if isinstance(data, str):
        return data

    routes = data.get("routes", [])
    if not routes:
        return "No route found."

    route = routes[0]
    summary = route.get("summary", {})
    total_distance = summary.get("distance", 0)
    total_duration = summary.get("duration", 0)

    hours = int(total_duration // 3600)
    minutes = int((total_duration % 3600) // 60)
    duration_str = f"{hours}h {minutes}min" if hours else f"{minutes} min"

    lines = [
        f"## Route Summary ({profile})\n",
        f"- **Total distance:** {total_distance:.1f} km",
        f"- **Total duration:** {duration_str}",
        f"- **Waypoints:** {len(coordinates)}",
    ]

    # Per-segment breakdown
    segments = route.get("segments", [])
    if segments and len(segments) > 1:
        lines.append("\n### Segments\n")
        for i, seg in enumerate(segments, 1):
            seg_dist = seg.get("distance", 0)
            seg_dur = seg.get("duration", 0)
            seg_h = int(seg_dur // 3600)
            seg_m = int((seg_dur % 3600) // 60)
            seg_dur_str = f"{seg_h}h {seg_m}min" if seg_h else f"{seg_m} min"
            lines.append(f"- Segment {i}: {seg_dist:.1f} km, {seg_dur_str}")

    return "\n".join(lines)


@mcp.tool()
async def geocode(query: str, country: str | None = None) -> str:
    """Geocode a place name to coordinates.

    Args:
        query: Place name or address to search for.
        country: Optional ISO 3166-1 alpha-2 country code to restrict results (e.g. "FI", "DE", "IT").

    Returns:
        List of matching locations with coordinates.
    """
    if not query or len(query) < 2:
        return "Error: query must be at least 2 characters"

    result = await _geocode(query, country)

    if "error" in result:
        return result["error"]

    results = result["results"]
    lines = [f"Found {len(results)} result(s):\n"]
    for r in results:
        lines.append(
            f"- **{r['name']}** — {r['label']}\n"
            f"  Coordinates: [{r['coordinates'][0]:.6f}, {r['coordinates'][1]:.6f}] (confidence: {r['confidence']})"
        )

    return "\n".join(lines)


@mcp.tool()
async def driving_time(
    from_coords: list[float],
    to_coords: list[float],
    profile: str = "driving-car",
) -> str:
    """Get driving time and distance between two points.

    Args:
        from_coords: Start point as [longitude, latitude].
        to_coords: End point as [longitude, latitude].
        profile: Routing profile (default: driving-car).

    Returns:
        Distance in km and duration.
    """
    return await calculate_route([from_coords, to_coords], profile)


@mcp.tool()
async def isochrone(
    location: list[float],
    range_seconds: list[int],
    profile: str = "driving-car",
) -> str:
    """Calculate reachability areas (isochrones) from a location.

    Shows what area is reachable within given time limits.

    Args:
        location: Center point as [longitude, latitude].
        range_seconds: List of time limits in seconds (e.g. [1800, 3600] for 30min and 1h).
        profile: Routing profile (default: driving-car).

    Returns:
        Isochrone areas with reachable distance for each time limit.
    """
    if not location or len(location) != 2:
        return "Error: location must be [longitude, latitude]"
    if not range_seconds:
        return "Error: at least one range value required"
    if profile not in VALID_PROFILES:
        return f"Error: invalid profile '{profile}'. Valid: {', '.join(sorted(VALID_PROFILES))}"

    body = {
        "locations": [location],
        "range": range_seconds,
        "range_type": "time",
    }

    data = await _api_post(f"/v2/isochrones/{profile}", body)
    if isinstance(data, str):
        return data

    features = data.get("features", [])
    if not features:
        return "No isochrone data returned."

    lines = [f"## Isochrones from [{location[0]:.4f}, {location[1]:.4f}] ({profile})\n"]
    for feat in features:
        props = feat.get("properties", {})
        value = props.get("value", 0)
        area = props.get("area", 0)
        minutes = value / 60
        area_km2 = area / 1_000_000
        lines.append(f"- **{minutes:.0f} min**: ~{area_km2:.1f} km² reachable")

    return "\n".join(lines)


@mcp.tool()
async def distance_matrix(
    locations: list[list[float]],
    profile: str = "driving-car",
) -> str:
    """Calculate driving times between all pairs of locations (N×N matrix).

    Useful for comparing multiple route options or finding the optimal order.

    Args:
        locations: List of [longitude, latitude] pairs (2-50 locations).
        profile: Routing profile (default: driving-car).

    Returns:
        Matrix of durations (minutes) and distances (km) between all pairs.
    """
    if not locations or len(locations) < 2:
        return "Error: at least 2 locations required"
    if len(locations) > 50:
        return "Error: maximum 50 locations"
    if profile not in VALID_PROFILES:
        return f"Error: invalid profile '{profile}'. Valid: {', '.join(sorted(VALID_PROFILES))}"

    body = {
        "locations": locations,
        "metrics": ["duration", "distance"],
        "units": "km",
    }

    data = await _api_post(f"/v2/matrix/{profile}", body)
    if isinstance(data, str):
        return data

    durations = data.get("durations", [])
    distances = data.get("distances", [])

    if not durations:
        return "No matrix data returned."

    n = len(locations)
    lines = [f"## Distance Matrix ({n} locations, {profile})\n"]
    lines.append("### Durations (minutes)\n")

    # Header
    header = "|     | " + " | ".join(f"#{i + 1}" for i in range(n)) + " |"
    sep = "| --- | " + " | ".join("---" for _ in range(n)) + " |"
    lines.append(header)
    lines.append(sep)

    for i in range(n):
        row = f"| #{i + 1} |"
        for j in range(n):
            dur = durations[i][j] if durations[i][j] is not None else 0
            row += f" {dur / 60:.0f} |"
        lines.append(row)

    if distances:
        lines.append("\n### Distances (km)\n")
        lines.append(header)
        lines.append(sep)
        for i in range(n):
            row = f"| #{i + 1} |"
            for j in range(n):
                dist = distances[i][j] if distances[i][j] is not None else 0
                row += f" {dist:.0f} |"
            lines.append(row)

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
