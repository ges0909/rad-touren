"""MCP server wrapping the Waymarked Trails API for hiking and cycling route discovery.

Uses lib.routes for all API logic. This file provides MCP tool declarations
and formats structured results into human-readable strings.
"""

from fastmcp import FastMCP
from lib.routes import (
    get_route_details as _details,
)
from lib.routes import (
    get_route_segments as _segments,
)
from lib.routes import (
    search_routes as _search,
)

mcp = FastMCP("Waymarked Trails Routes")

GROUP_LABELS = {
    "INT": "International",
    "NAT": "National",
    "REG": "Regional",
    "LOC": "Lokal",
}


@mcp.tool()
async def search_routes(
    query: str,
    activity: str = "hiking",
    limit: int = 10,
) -> str:
    """Search for marked hiking or cycling routes by name.

    Args:
        query: Search query — route name, region, or keyword.
        activity: Type of route — "hiking" or "cycling"
        limit: Maximum number of results (1-20)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"

    result = await _search(query.strip(), activity, limit)

    if "error" in result:
        return result["error"]

    routes = result["routes"]
    emoji = "🥾" if activity == "hiking" else "🚴"
    lines = [f"{emoji} Gefunden: {len(routes)} Route(n) für '{query}'\n"]
    for r in routes:
        ref_str = f" [{r['ref']}]" if r["ref"] else ""
        group_label = GROUP_LABELS.get(r["group"], r["group"])
        type_str = "Rundweg" if r["type"] == "loop" else "Strecke"
        lines.append(f"- **{r['name']}**{ref_str} ({group_label}, {type_str})\n  ID: {r['id']}")

    return "\n".join(lines)


@mcp.tool()
async def get_route_details(
    route_id: int,
    activity: str = "hiking",
) -> str:
    """Get detailed information about a specific route.

    Args:
        route_id: OSM relation ID of the route (from search_routes results)
        activity: Type of route — "hiking" or "cycling"
    """
    if not route_id or route_id < 1:
        return "Error: route_id must be a positive integer"

    result = await _details(route_id, activity)

    if "error" in result:
        return result["error"]

    group_label = GROUP_LABELS.get(result["group"], result["group"])
    length_str = (
        f"{result['official_length_km']} km (offiziell)"
        if result["official_length_km"]
        else f"{result['length_km']} km"
    )

    lines = [f"# {result['name']}"]
    if result["ref"]:
        lines.append(f"**Ref:** {result['ref']}")
    lines.append(f"**Netzwerk:** {group_label}")
    lines.append(f"**Typ:** {'Rundweg' if result['type'] == 'loop' else 'Strecke'}")
    lines.append(f"**Länge:** {length_str}")
    if result["operator"]:
        lines.append(f"**Betreiber:** {result['operator']}")
    if result["description"]:
        lines.append(f"\n{result['description']}")
    if result["url"]:
        lines.append(f"\n🔗 {result['url']}")
    if result["subroutes"]:
        lines.append(f"\n## Teilstrecken ({len(result['subroutes'])})")
        for sr in result["subroutes"][:10]:
            lines.append(f"- {sr['name']} (ID: {sr['id']})")

    lines.append(f"\nQuelle: https://{activity}.waymarkedtrails.org/#route?id={route_id}")
    lines.append(f"OSM: https://www.openstreetmap.org/relation/{route_id}")

    return "\n".join(lines)


@mcp.tool()
async def search_routes_in_region(
    region: str,
    activity: str = "hiking",
    limit: int = 15,
) -> str:
    """Search for routes in a specific region or area.

    Args:
        region: Region or area name (e.g. "Märkische Schweiz", "Fläming", "Uckermark")
        activity: Type of route — "hiking" or "cycling"
        limit: Maximum number of results (1-20)
    """
    return await search_routes(region, activity, limit)


@mcp.tool()
async def get_route_segments(
    route_id: int,
    activity: str = "hiking",
) -> str:
    """Get the waypoints/segments of a route for understanding its path.

    Args:
        route_id: OSM relation ID of the route
        activity: Type of route — "hiking" or "cycling"
    """
    if not route_id or route_id < 1:
        return "Error: route_id must be a positive integer"

    result = await _segments(route_id, activity)

    if "error" in result:
        return result["error"]

    lines = [
        f"# Routenverlauf: {result['name']}",
        f"**Gesamtlänge:** {result['length_km']} km",
        f"**Typ:** {'Rundweg' if result['type'] == 'loop' else 'Strecke'}",
    ]

    if result["subroutes"]:
        lines.append(f"\n## Etappen ({len(result['subroutes'])})\n")
        for i, sr in enumerate(result["subroutes"], 1):
            ref_part = f" [{sr['ref']}]" if sr.get("ref") else ""
            lines.append(f"{i}. → {sr['name']}{ref_part} (ID: {sr['id']})")
    elif result["itinerary"]:
        lines.append("\n## Verlauf\n")
        lines.append(" → ".join(result["itinerary"]))

    lines.append(f"\nQuelle: https://{activity}.waymarkedtrails.org/#route?id={route_id}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
