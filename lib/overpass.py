"""Overpass API client — POI search along routes."""

from typing import Any

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT = 60
HEADERS = {"User-Agent": "TripPlanner/1.0 (POI search)"}

POI_CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "beer_garden": [("amenity", "biergarten")],
    "cafe": [("amenity", "cafe")],
    "restaurant": [("amenity", "restaurant")],
    "swimming": [("leisure", "swimming_area"), ("sport", "swimming")],
    "bicycle_repair": [("shop", "bicycle")],
    "drinking_water": [("amenity", "drinking_water")],
    "viewpoint": [("tourism", "viewpoint")],
    "museum": [("tourism", "museum")],
    "artwork": [("tourism", "artwork")],
    "gallery": [("tourism", "gallery")],
    "castle": [("historic", "castle")],
    "memorial": [("historic", "memorial")],
    "ruins": [("historic", "ruins")],
    "church": [("amenity", "place_of_worship")],
    "picnic": [("tourism", "picnic_site")],
}

PRESETS: dict[str, list[str]] = {
    "einkehr": ["beer_garden", "cafe", "restaurant"],
    "badestellen": ["swimming"],
    "sehenswuerdigkeiten": ["museum", "castle", "memorial", "viewpoint"],
    "kunst": ["artwork", "gallery"],
    "radservice": ["bicycle_repair", "drinking_water"],
    "rast": ["picnic", "drinking_water", "viewpoint"],
}


def build_query(
    categories: list[str], poly_coords: str, radius: int = 500
) -> str:
    """Build Overpass QL query for categories around a polyline.

    Args:
        categories: List of POI category names.
        poly_coords: Comma-separated "lat,lon,lat,lon,..." string.
        radius: Search radius in meters.
    """
    filters: list[str] = []
    for cat in categories:
        tags = POI_CATEGORIES.get(cat, [])
        for key, value in tags:
            filters.append(f'  nwr["{key}"="{value}"](around:{radius},{poly_coords});')

    if not filters:
        return ""

    return "[out:json][timeout:30];\n(\n" + "\n".join(filters) + "\n);\nout center tags;\n"


async def search_pois(query: str) -> dict[str, Any]:
    """Execute an Overpass QL query and return POI results.

    Args:
        query: Complete Overpass QL query string.

    Returns:
        Dict with "pois" list of {name, lat, lon, category, tags}.
    """
    if not query:
        return {"error": "Empty query"}

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query})
        resp.raise_for_status()
        data = resp.json()

    elements = data.get("elements", [])

    # Deduplicate by name + approximate location
    seen: set[str] = set()
    pois: list[dict[str, Any]] = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        lat = el.get("center", {}).get("lat", el.get("lat", 0))
        lon = el.get("center", {}).get("lon", el.get("lon", 0))
        key = f"{name}:{lat:.4f}:{lon:.4f}"
        if key in seen:
            continue
        seen.add(key)

        # Determine category
        category = ""
        for cat, tag_list in POI_CATEGORIES.items():
            for tag_key, tag_val in tag_list:
                if tags.get(tag_key) == tag_val:
                    category = cat
                    break
            if category:
                break

        pois.append({
            "name": name or tags.get("operator", "Unnamed"),
            "lat": lat,
            "lon": lon,
            "category": category,
            "tags": tags,
        })

    return {"pois": pois}
