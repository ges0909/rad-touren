"""BRouter cycling/hiking routing client + Nominatim geocoding."""

import asyncio
from typing import Any
from urllib.parse import urlencode

import httpx

BROUTER_BASE_URL = "https://brouter.de/brouter"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "trip-planner/1.0 (cycling tour planner)"
TIMEOUT = 60

# Rate limiter for Nominatim (1 req/sec)
_nominatim_lock = asyncio.Lock()
_last_nominatim_call: float = 0.0


async def calculate_route(
    waypoints: list[list[float]],
    profile: str = "trekking",
    format: str = "gpx",
    alternativeidx: int = 0,
    nogos: list[dict[str, Any]] | None = None,
    track_name: str | None = None,
) -> dict[str, Any]:
    """Calculate a cycling/hiking route via BRouter.

    Args:
        waypoints: List of [longitude, latitude] pairs (min 2).
        profile: BRouter profile (trekking, fastbike, safety, shortest, etc.).
        format: Output format — "gpx" or "geojson".
        alternativeidx: Alternative route index (0-3).
        nogos: Optional no-go areas [{lon, lat, radius}, ...].
        track_name: Optional name to insert into GPX track.

    Returns:
        Dict with gpx/geojson content, distance_km, duration_min.
    """
    if len(waypoints) < 2:
        return {"error": "At least 2 waypoints required."}
    if alternativeidx < 0 or alternativeidx > 3:
        return {"error": f"Invalid alternative index {alternativeidx}. Valid: 0-3."}

    lonlats = "|".join(f"{lon},{lat}" for lon, lat in waypoints)
    params: dict[str, str] = {
        "lonlats": lonlats,
        "profile": profile,
        "format": format,
        "alternativeidx": str(alternativeidx),
    }

    if nogos:
        nogos_str = "|".join(
            f"{n['lon']},{n['lat']},{n.get('radius', 20)}" for n in nogos
        )
        params["nogos"] = nogos_str

    url = f"{BROUTER_BASE_URL}?{urlencode(params)}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content = resp.text

    return {"content": content, "format": format}


async def search_location(
    query: str, country_code: str = "de", limit: int = 5
) -> dict[str, Any]:
    """Search for locations via Nominatim geocoding.

    Args:
        query: Place name or address.
        country_code: ISO 3166-1 alpha-2 country code.
        limit: Max results (1-40).

    Returns:
        Dict with "results" list of {name, lat, lon, display_name}.
    """
    import time

    global _last_nominatim_call

    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "countrycodes": country_code,
    }

    # Rate limit: 1 request per second
    async with _nominatim_lock:
        now = time.time()
        wait = max(0, 1.0 - (now - _last_nominatim_call))
        if wait > 0:
            await asyncio.sleep(wait)

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                NOMINATIM_BASE_URL,
                params=params,
                headers={"User-Agent": NOMINATIM_USER_AGENT},
            )
            resp.raise_for_status()
            data = resp.json()

        _last_nominatim_call = time.time()

    if not data:
        return {"error": f"No results found for '{query}'"}

    results: list[dict[str, Any]] = []
    for r in data:
        results.append({
            "name": r.get("display_name", "?"),
            "lat": float(r.get("lat", 0)),
            "lon": float(r.get("lon", 0)),
            "type": r.get("type", ""),
        })

    return {"results": results}
