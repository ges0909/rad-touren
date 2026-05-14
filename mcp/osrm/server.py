"""MCP server wrapping the public OSRM API for car routing with GPX export.

OSRM (Open Source Routing Machine) provides fast, accurate street routing
based on OpenStreetMap data. The public demo server requires no API key.

Usage:
    fastmcp run server.py
"""

from pathlib import Path
from datetime import datetime, timezone

import httpx
from fastmcp import FastMCP

mcp = FastMCP("OSRM Car Routing")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://router.project-osrm.org"
PROFILE = "driving"  # OSRM public server supports: driving, walking, cycling


# ---------------------------------------------------------------------------
# Polyline decoding (Google Encoded Polyline Algorithm)
# ---------------------------------------------------------------------------


def _decode_polyline(encoded: str, precision: int = 5) -> list[tuple[float, float]]:
    """Decode a Google-encoded polyline string into (lat, lon) pairs."""
    coords = []
    index = 0
    lat = 0
    lng = 0
    factor = 10**precision

    while index < len(encoded):
        # Decode latitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (~(result >> 1) if (result & 1) else (result >> 1))

        # Decode longitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += (~(result >> 1) if (result & 1) else (result >> 1))

        coords.append((lat / factor, lng / factor))

    return coords


# ---------------------------------------------------------------------------
# GPX generation
# ---------------------------------------------------------------------------


def _coords_to_gpx(
    coords: list[tuple[float, float]],
    name: str = "route",
    waypoints: list[dict] | None = None,
) -> str:
    """Convert coordinate list to GPX XML string.

    Args:
        coords: List of (lat, lon) tuples from polyline decode.
        name: Track name.
        waypoints: Optional list of {"name": str, "lat": float, "lon": float}.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="osrm-mcp"',
        '     xmlns="http://www.topografix.com/GPX/1/1">',
        "  <metadata>",
        f"    <name>{name}</name>",
        f"    <time>{timestamp}</time>",
        "  </metadata>",
    ]

    # Add waypoints (stations)
    if waypoints:
        for wp in waypoints:
            lines.append(
                f'  <wpt lat="{wp["lat"]:.6f}" lon="{wp["lon"]:.6f}">'
            )
            lines.append(f'    <name>{wp["name"]}</name>')
            lines.append("  </wpt>")

    # Add track
    lines.append("  <trk>")
    lines.append(f"    <name>{name}</name>")
    lines.append("    <trkseg>")
    for lat, lon in coords:
        lines.append(f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}"/>')
    lines.append("    </trkseg>")
    lines.append("  </trk>")
    lines.append("</gpx>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


async def _osrm_request(coordinates_str: str, **params) -> dict | str:
    """Make request to OSRM public server.

    Args:
        coordinates_str: Semicolon-separated "lon,lat" pairs.
        **params: Additional query parameters.
    """
    url = f"{BASE_URL}/route/v1/{PROFILE}/{coordinates_str}"

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return f"OSRM API error {e.response.status_code}: {e.response.text[:300]}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def calculate_car_route(
    waypoints: list[list[float]],
    overview: str = "full",
) -> str:
    """Calculate a car route between waypoints via OSRM.

    Returns distance, duration, and per-leg breakdown.
    No API key required (public OSRM demo server, OSM data).

    Args:
        waypoints: List of [longitude, latitude] coordinate pairs (min 2, max 100).
        overview: Geometry detail — "full" (default), "simplified", or "false".
    """
    if len(waypoints) < 2:
        return "Error: At least 2 waypoints required."
    if len(waypoints) > 100:
        return "Error: Maximum 100 waypoints supported."

    coords_str = ";".join(f"{lon},{lat}" for lon, lat in waypoints)

    data = await _osrm_request(
        coords_str,
        overview=overview,
        geometries="polyline",
        steps="false",
    )

    if isinstance(data, str):
        return data

    if data.get("code") != "Ok":
        return f"OSRM error: {data.get('message', 'Unknown error')}"

    route = data["routes"][0]
    distance_km = route["distance"] / 1000
    duration_min = route["duration"] / 60
    hours = int(duration_min // 60)
    minutes = int(duration_min % 60)

    lines = [
        "## Route Summary (car)",
        "",
        f"- **Total distance:** {distance_km:.1f} km",
        f"- **Total duration:** {hours}h {minutes:02d}min",
        f"- **Waypoints:** {len(waypoints)}",
        "",
    ]

    # Per-leg breakdown
    if "legs" in route and len(route["legs"]) > 1:
        lines.append("### Legs")
        lines.append("")
        for i, leg in enumerate(route["legs"]):
            leg_km = leg["distance"] / 1000
            leg_min = leg["duration"] / 60
            lh = int(leg_min // 60)
            lm = int(leg_min % 60)
            lines.append(
                f"- Leg {i + 1}: {leg_km:.1f} km, {lh}h {lm:02d}min"
            )

    return "\n".join(lines)


@mcp.tool()
async def route_to_gpx(
    waypoints: list[list[float]],
    output_path: str,
    track_name: str = "route",
    station_names: list[str] | None = None,
) -> str:
    """Calculate a car route and save it as a GPX file.

    The GPX contains the full road geometry as a track, plus optional
    named waypoints for the stations.

    Args:
        waypoints: List of [longitude, latitude] coordinate pairs (min 2).
        output_path: Absolute path where the GPX file will be saved.
        track_name: Name for the GPX track element.
        station_names: Optional list of station names (same length as waypoints).
    """
    if len(waypoints) < 2:
        return "Error: At least 2 waypoints required."

    coords_str = ";".join(f"{lon},{lat}" for lon, lat in waypoints)

    data = await _osrm_request(
        coords_str,
        overview="full",
        geometries="polyline",
    )

    if isinstance(data, str):
        return data

    if data.get("code") != "Ok":
        return f"OSRM error: {data.get('message', 'Unknown error')}"

    route = data["routes"][0]
    geometry = route["geometry"]

    # Decode polyline to coordinates
    coords = _decode_polyline(geometry)

    # Build waypoint list for GPX
    gpx_waypoints = None
    if station_names and len(station_names) == len(waypoints):
        gpx_waypoints = [
            {"name": name, "lon": wp[0], "lat": wp[1]}
            for name, wp in zip(station_names, waypoints)
        ]

    # Generate GPX
    gpx_content = _coords_to_gpx(coords, name=track_name, waypoints=gpx_waypoints)

    # Save file
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(gpx_content, encoding="utf-8")

    # Summary
    distance_km = route["distance"] / 1000
    duration_min = route["duration"] / 60
    hours = int(duration_min // 60)
    minutes = int(duration_min % 60)

    return (
        f"GPX saved to {output_path}\n"
        f"- Track points: {len(coords)}\n"
        f"- Distance: {distance_km:.1f} km\n"
        f"- Duration: {hours}h {minutes:02d}min\n"
        f"- Waypoints: {len(gpx_waypoints) if gpx_waypoints else 0}"
    )
