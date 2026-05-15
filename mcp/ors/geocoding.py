"""Geocoding client via OpenRouteService."""

import os
from typing import Any

import httpx

ORS_BASE_URL = "https://api.openrouteservice.org"
TIMEOUT = 30


def _get_api_key() -> str:
    """Get ORS API key from environment."""
    return os.environ.get("ORS_API_KEY", "")


async def geocode(query: str, country: str | None = None) -> dict[str, Any]:
    """Geocode a place name to coordinates.

    Args:
        query: Place name or address.
        country: Optional ISO 3166-1 alpha-2 country code.

    Returns:
        Dict with "results" list, each having name, label, coordinates [lon, lat], confidence.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "ORS_API_KEY not configured"}

    params: dict[str, str | int] = {
        "api_key": api_key,
        "text": query,
        "size": 5,
    }
    if country:
        params["boundary.country"] = country.upper()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{ORS_BASE_URL}/geocode/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    features: list[dict[str, Any]] = data.get("features", [])
    if not features:
        return {"error": f"No results found for '{query}'"}

    results: list[dict[str, Any]] = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [0, 0])
        results.append(
            {
                "name": props.get("name", "?"),
                "label": props.get("label", "?"),
                "coordinates": coords,  # [lon, lat]
                "confidence": props.get("confidence", 0),
            }
        )

    return {"results": results}
