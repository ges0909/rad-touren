"""MCP server for POI search along cycling routes via Overpass API (OpenStreetMap).

Uses lib.overpass for query building and API calls. GPX parsing stays here
as it's MCP-specific (file system access).
"""

import sys
from pathlib import Path

import gpxpy
from fastmcp import FastMCP

# Add lib/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.overpass import build_query, search_pois, POI_CATEGORIES, PRESETS

mcp = FastMCP("Overpass POI Search")


def _sample_track_points(gpx_path: str, max_points: int = 80) -> list[tuple[float, float]]:
    """Read GPX file and return sampled (lat, lon) points."""
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

    step = len(all_points) / max_points
    sampled = [all_points[int(i * step)] for i in range(max_points)]
    if sampled[-1] != all_points[-1]:
        sampled.append(all_points[-1])
    return sampled


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
        if preset not in PRESETS:
            return f"Error: unknown preset '{preset}'. Available: {', '.join(PRESETS)}"
        cats = PRESETS[preset]
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

    # Build query and execute
    poly_coords = ",".join(f"{lat},{lon}" for lat, lon in points)
    query = build_query(cats, poly_coords, radius)
    if not query:
        return "Error: no valid tag filters for the given categories"

    result = await search_pois(query)

    if "error" in result:
        return result["error"]

    pois = result["pois"]
    if not pois:
        return "No POIs found along the route for the requested categories."

    lines = [f"Found {len(pois)} POI(s) along the route:\n"]
    for poi in pois:
        detail_parts: list[str] = []
        tags = poi.get("tags", {})
        if tags.get("cuisine"):
            detail_parts.append(f"Küche: {tags['cuisine']}")
        if tags.get("opening_hours"):
            detail_parts.append(f"Öffnungszeiten: {tags['opening_hours']}")
        if tags.get("website"):
            detail_parts.append(tags["website"])

        detail_str = f" — {', '.join(detail_parts)}" if detail_parts else ""
        lines.append(
            f"- **{poi['name']}** ({poi['category']}) [{poi['lat']:.5f}, {poi['lon']:.5f}]{detail_str}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
