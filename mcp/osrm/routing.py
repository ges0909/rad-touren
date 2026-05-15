"""OSRM routing client — car route calculation and polyline decoding."""

from typing import Any

import httpx

OSRM_BASE_URL = "https://router.project-osrm.org"
TIMEOUT = 60


def decode_polyline(encoded: str, precision: int = 5) -> list[tuple[float, float]]:
    """Decode a Google-encoded polyline string into (lat, lon) pairs."""
    coords: list[tuple[float, float]] = []
    index = 0
    lat = 0
    lng = 0
    factor = 10**precision

    while index < len(encoded):
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += ~(result >> 1) if (result & 1) else (result >> 1)

        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += ~(result >> 1) if (result & 1) else (result >> 1)

        coords.append((lat / factor, lng / factor))

    return coords


async def calculate_car_route(
    waypoints: list[list[float]],
    overview: str = "full",
) -> dict[str, Any]:
    """Calculate a car route between waypoints via OSRM.

    Args:
        waypoints: List of [longitude, latitude] pairs (min 2).
        overview: Geometry detail — "full", "simplified", or "false".

    Returns:
        Dict with distance_km, duration_min, waypoints, geometry.
    """
    if len(waypoints) < 2:
        return {"error": "At least 2 waypoints required."}

    coords_str = ";".join(f"{lon},{lat}" for lon, lat in waypoints)
    url = f"{OSRM_BASE_URL}/route/v1/driving/{coords_str}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(url, params={"overview": overview, "geometries": "polyline"})
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok":
        return {"error": data.get("message", "Routing failed")}

    route = data["routes"][0]
    geometry = decode_polyline(route["geometry"]) if overview != "false" else []

    return {
        "distance_km": round(route["distance"] / 1000, 1),
        "duration_min": round(route["duration"] / 60),
        "waypoints": [[wp[1], wp[0]] for wp in waypoints],  # [lat, lon]
        "geometry": geometry,  # [(lat, lon), ...]
    }


async def driving_time(from_coords: list[float], to_coords: list[float]) -> dict[str, Any]:
    """Get driving time and distance between two points via OSRM.

    Args:
        from_coords: [longitude, latitude]
        to_coords: [longitude, latitude]
    """
    coords_str = f"{from_coords[0]},{from_coords[1]};{to_coords[0]},{to_coords[1]}"
    url = f"{OSRM_BASE_URL}/route/v1/driving/{coords_str}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(url, params={"overview": "false"})
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok":
        return {"error": data.get("message", "Routing failed")}

    route = data["routes"][0]
    return {
        "distance_km": round(route["distance"] / 1000, 1),
        "duration_min": round(route["duration"] / 60),
    }


def coords_to_gpx(
    coords: list[tuple[float, float]],
    name: str = "route",
    waypoints: list[dict[str, Any]] | None = None,
) -> str:
    """Convert coordinate list to GPX XML string.

    Args:
        coords: List of (lat, lon) tuples.
        name: Track name.
        waypoints: Optional list of {"name": str, "lat": float, "lon": float}.
    """
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="trip-planner"',
        '     xmlns="http://www.topografix.com/GPX/1/1">',
        "  <metadata>",
        f"    <name>{name}</name>",
        f"    <time>{timestamp}</time>",
        "  </metadata>",
    ]

    if waypoints:
        for wp in waypoints:
            lines.append(f'  <wpt lat="{wp["lat"]:.6f}" lon="{wp["lon"]:.6f}">')
            lines.append(f"    <name>{wp['name']}</name>")
            lines.append("  </wpt>")

    lines.append("  <trk>")
    lines.append(f"    <name>{name}</name>")
    lines.append("    <trkseg>")
    for lat, lon in coords:
        lines.append(f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}"/>')
    lines.append("    </trkseg>")
    lines.append("  </trk>")
    lines.append("</gpx>")

    return "\n".join(lines)


async def route_to_gpx(
    waypoints: list[list[float]],
    output_path: str,
    track_name: str = "route",
    station_names: list[str] | None = None,
) -> dict[str, Any]:
    """Calculate a car route and save as GPX file.

    Args:
        waypoints: List of [longitude, latitude] pairs.
        output_path: Path where GPX file will be saved.
        track_name: Name for the GPX track.
        station_names: Optional station names (same length as waypoints).
    """
    from pathlib import Path

    result = await calculate_car_route(waypoints, overview="full")
    if "error" in result:
        return result

    geometry = result["geometry"]

    gpx_waypoints = None
    if station_names and len(station_names) == len(waypoints):
        gpx_waypoints = [
            {"name": name, "lon": wp[0], "lat": wp[1]}
            for name, wp in zip(station_names, waypoints, strict=True)
        ]

    gpx_content = coords_to_gpx(geometry, name=track_name, waypoints=gpx_waypoints)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(gpx_content, encoding="utf-8")

    return {
        "path": output_path,
        "track_points": len(geometry),
        "distance_km": result["distance_km"],
        "duration_min": result["duration_min"],
        "waypoint_count": len(gpx_waypoints) if gpx_waypoints else 0,
    }
