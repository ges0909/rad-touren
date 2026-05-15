"""Waymarked Trails API client — search for marked hiking and cycling routes."""

from typing import Any

import httpx

BASE_URLS = {
    "hiking": "https://hiking.waymarkedtrails.org/api/v1",
    "cycling": "https://cycling.waymarkedtrails.org/api/v1",
}
TIMEOUT = 30
HEADERS = {
    "User-Agent": "TourPlanner/1.0 (tour planning tool)",
    "Accept": "application/json",
}


async def search_routes(
    query: str, activity: str = "hiking", limit: int = 10
) -> dict[str, Any]:
    """Search for marked routes by name or region.

    Args:
        query: Route name, region, or keyword.
        activity: "hiking" or "cycling".
        limit: Max results (1-20).
    """
    if activity not in BASE_URLS:
        return {"error": f"activity must be 'hiking' or 'cycling'"}

    base_url = BASE_URLS[activity]

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        resp = await client.get(f"{base_url}/list/search", params={"query": query, "limit": limit})
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return {"error": f"No routes found for '{query}'"}

    routes: list[dict[str, Any]] = []
    for r in results:
        routes.append({
            "id": r.get("id"),
            "name": r.get("name", "?"),
            "ref": r.get("ref", ""),
            "group": r.get("group", ""),
            "type": "loop" if r.get("linear") == "no" else "linear",
        })

    return {"routes": routes}


async def get_route_details(route_id: int, activity: str = "hiking") -> dict[str, Any]:
    """Get detailed information about a specific route.

    Args:
        route_id: OSM relation ID.
        activity: "hiking" or "cycling".
    """
    if activity not in BASE_URLS:
        return {"error": f"activity must be 'hiking' or 'cycling'"}

    base_url = BASE_URLS[activity]

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        resp = await client.get(f"{base_url}/details/relation/{route_id}")
        resp.raise_for_status()
        data = resp.json()

    route_info = data.get("route", {})
    length_m = route_info.get("length", 0) if isinstance(route_info, dict) else 0

    return {
        "id": data.get("id"),
        "name": data.get("name", "?"),
        "ref": data.get("ref", ""),
        "group": data.get("group", ""),
        "type": "loop" if data.get("linear") == "no" else "linear",
        "length_km": round(length_m / 1000, 1),
        "official_length_km": round(data["official_length"] / 1000, 1) if data.get("official_length") else None,
        "operator": data.get("operator", ""),
        "description": data.get("description", ""),
        "url": data.get("url", ""),
        "subroutes": [
            {"id": sr.get("id"), "name": sr.get("name", "?")}
            for sr in (data.get("subroutes") or {}).values()
        ],
    }
