"""MCP server for POI search along cycling routes via Overpass API (OpenStreetMap)."""

import math
from pathlib import Path

import gpxpy
import httpx
from fastmcp import FastMCP

mcp = FastMCP("Overpass POI Search")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# POI categories mapped to Overpass tag filters.
# Each category is a list of (key, value_regex) pairs combined with OR.
POI_CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "beer_garden": [
        ("amenity", "biergarten"),
        ("beer_garden", "yes"),
    ],
    "cafe": [
        ("amenity", "cafe"),
    ],
    "restaurant": [
        ("amenity", "restaurant"),
    ],
    "swimming": [
        ("leisure", "swimming_area"),
        ("leisure", "bathing_place"),
        ("sport", "swimming"),
        ("natural", "beach"),
    ],
    "bicycle_repair": [
        ("shop", "bicycle"),
        ("amenity", "bicycle_repair_station"),
    ],
    "drinking_water": [
        ("amenity", "drinking_water"),
    ],
    "viewpoint": [
        ("tourism", "viewpoint"),
    ],
    "museum": [
        ("tourism", "museum"),
    ],
    "artwork": [
        ("tourism", "artwork"),
    ],
    "gallery": [
        ("tourism", "gallery"),
        ("shop", "art"),
    ],
    "castle": [
        ("historic", "castle"),
        ("historic", "manor"),
    ],
    "memorial": [
        ("historic", "memorial"),
        ("historic", "monument"),
    ],
    "ruins": [
        ("historic", "ruins"),
    ],
    "church": [
        ("amenity", "place_of_worship"),
    ],
    "picnic": [
        ("tourism", "picnic_site"),
        ("leisure", "picnic_table"),
    ],
}

# Grouped presets matching the steering file emoji categories
CATEGORY_PRESETS: dict[str, list[str]] = {
    "einkehr": ["beer_garden", "cafe", "restaurant"],
    "badestellen": ["swimming"],
    "sehenswuerdigkeiten": ["museum", "castle", "memorial", "ruins", "church", "viewpoint"],
    "kunst": ["artwork", "gallery"],
    "radservice": ["bicycle_repair", "drinking_water"],
    "rast": ["picnic", "drinking_water", "viewpoint"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_track_points(gpx_path: str, max_points: int = 80) -> list[tuple[float, float]]:
    """Read GPX file and return sampled (lat, lon) points.

    Overpass around filter has a practical limit on polyline length.
    We sample evenly to stay within ~80 points.
    """
    path = Path(gpx_path)
    if not path.exists():
        raise FileNotFoundError(f"GPX file not found: {gpx_path}")

    with open(path) as f:
        gpx = gpxpy.parse(f)

    all_points: list[tuple[float, float]] = []
    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                all_points.append((pt.latitude, pt.longitude))

    if not all_points:
        raise ValueError("GPX file contains no track points")

    if len(all_points) <= max_points:
        return all_points

    # Sample evenly
    step = len(all_points) / max_points
    sampled = [all_points[int(i * step)] for i in range(max_points)]
    # Always include last point
    if sampled[-1] != all_points[-1]:
        sampled.append(all_points[-1])
    return sampled


def _build_around_poly(points: list[tuple[float, float]]) -> str:
    """Build Overpass around:radius,lat,lon,lat,lon,... polyline string."""
    coords = ",".join(f"{lat},{lon}" for lat, lon in points)
    return coords


def _build_query(
    categories: list[str],
    poly_coords: str,
    radius: int,
) -> str:
    """Build Overpass QL query for given categories around a polyline."""
    filters: list[str] = []
    for cat in categories:
        tags = POI_CATEGORIES.get(cat, [])
        for key, value in tags:
            filters.append(
                f'  nwr["{key}"="{value}"](around:{radius},{poly_coords});'
            )

    if not filters:
        return ""

    query = "[out:json][timeout:30];\n(\n"
    query += "\n".join(filters)
    query += "\n);\nout center tags;\n"
    return query


def _format_results(elements: list[dict], categories: list[str]) -> str:
    """Format Overpass JSON elements into readable text."""
    if not elements:
        return "No POIs found along the route for the requested categories."

    # Deduplicate by name+type
    seen: set[str] = set()
    pois: list[dict] = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        # Use center coordinates for ways/relations
        lat = el.get("center", {}).get("lat", el.get("lat", 0))
        lon = el.get("center", {}).get("lon", el.get("lon", 0))
        key = f"{name}:{lat:.4f}:{lon:.4f}"
        if key in seen:
            continue
        seen.add(key)
        pois.append({"tags": tags, "lat": lat, "lon": lon})

    lines = [f"Found {len(pois)} POI(s) along the route:\n"]

    for poi in pois:
        tags = poi["tags"]
        name = tags.get("name", "Unnamed")
        lat, lon = poi["lat"], poi["lon"]

        # Determine type
        poi_type = (
            tags.get("amenity")
            or tags.get("tourism")
            or tags.get("leisure")
            or tags.get("historic")
            or tags.get("shop")
            or tags.get("sport")
            or tags.get("natural")
            or "poi"
        )

        # Extra details
        details: list[str] = []
        if tags.get("cuisine"):
            details.append(f"Küche: {tags['cuisine']}")
        if tags.get("opening_hours"):
            details.append(f"Öffnungszeiten: {tags['opening_hours']}")
        if tags.get("website"):
            details.append(tags["website"])
        if tags.get("phone"):
            details.append(tags["phone"])
        if tags.get("description"):
            details.append(tags["description"])

        detail_str = f" — {', '.join(details)}" if details else ""
        lines.append(f"- **{name}** ({poi_type}) [{lat:.5f}, {lon:.5f}]{detail_str}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_pois_along_route(
    gpx_path: str,
    categories: list[str] | None = None,
    preset: str | None = None,
    radius: int = 500,
) -> str:
    """Search for points of interest along a GPX route using OpenStreetMap data.

    Uses the Overpass API to find POIs within a buffer around the route.
    Either specify individual categories or use a preset.

    Args:
        gpx_path: Absolute path to the GPX file
        categories: List of POI categories to search for. Available:
            beer_garden, cafe, restaurant, swimming, bicycle_repair,
            drinking_water, viewpoint, museum, artwork, gallery, castle,
            memorial, ruins, church, picnic
        preset: Use a preset instead of individual categories. Available:
            einkehr (beer gardens, cafés, restaurants),
            badestellen (swimming spots),
            sehenswuerdigkeiten (museums, castles, memorials, viewpoints),
            kunst (artwork, galleries),
            radservice (bicycle repair, drinking water),
            rast (picnic sites, drinking water, viewpoints)
        radius: Search radius in meters around the route (default: 500, max: 2000)
    """
    if not gpx_path:
        return "Error: gpx_path is required"
    if radius < 50 or radius > 2000:
        return "Error: radius must be between 50 and 2000 meters"

    # Resolve categories
    cats: list[str] = []
    if preset:
        if preset not in CATEGORY_PRESETS:
            return f"Error: unknown preset '{preset}'. Available: {', '.join(CATEGORY_PRESETS)}"
        cats = CATEGORY_PRESETS[preset]
    elif categories:
        invalid = [c for c in categories if c not in POI_CATEGORIES]
        if invalid:
            return f"Error: unknown categories: {', '.join(invalid)}. Available: {', '.join(POI_CATEGORIES)}"
        cats = categories
    else:
        return "Error: specify either 'categories' or 'preset'"

    # Read and sample GPX
    try:
        points = _sample_track_points(gpx_path)
    except (FileNotFoundError, ValueError) as e:
        return f"Error: {e}"

    poly_coords = _build_around_poly(points)
    query = _build_query(cats, poly_coords, radius)
    if not query:
        return "Error: no valid tag filters for the given categories"

    # Query Overpass API
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(
                OVERPASS_URL,
                data={"data": query},
                headers={"User-Agent": "overpass-mcp/1.0 (cycling tour planner)"},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            return f"Overpass API error {e.response.status_code}: {e.response.text[:200]}"
        except httpx.RequestError as e:
            return f"Request error: {e}"

    elements = data.get("elements", [])
    return _format_results(elements, cats)


if __name__ == "__main__":
    mcp.run()
