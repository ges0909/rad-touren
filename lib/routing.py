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


async def driving_time(
    from_coords: list[float], to_coords: list[float]
) -> dict[str, Any]:
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
