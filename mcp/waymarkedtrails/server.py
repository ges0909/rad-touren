"""MCP server wrapping the Waymarked Trails API for hiking and cycling route discovery.

Waymarked Trails (https://waymarkedtrails.org) provides data about marked
recreational routes from OpenStreetMap. This server exposes search and detail
endpoints for hiking and cycling routes.
"""

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Waymarked Trails Routes")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ACTIVITIES = ("hiking", "cycling")

BASE_URLS = {
    "hiking": "https://hiking.waymarkedtrails.org/api/v1",
    "cycling": "https://cycling.waymarkedtrails.org/api/v1",
}

# Route group descriptions (network level)
GROUP_LABELS = {
    "INT": "International",
    "NAT": "National",
    "REG": "Regional",
    "LOC": "Lokal",
    "NDS": "Niedersachsen",  # state-level in some regions
}


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


async def _get_json(activity: str, path: str) -> dict | list | str:
    """Make GET request to Waymarked Trails API and return JSON or error string."""
    if activity not in VALID_ACTIVITIES:
        return f"Error: activity must be one of {VALID_ACTIVITIES}"

    url = f"{BASE_URLS[activity]}{path}"
    headers = {
        "User-Agent": "WaymarkedTrailsMCP/1.0 (tour planning tool)",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error {e.response.status_code}: {e.response.text[:200]}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_route_summary(route: dict, activity: str) -> str:
    """Format a route search result into a readable line."""
    name = route.get("name", "Unbenannt")
    ref = route.get("ref", "")
    rid = route.get("id", "?")
    group = route.get("group", "")
    group_label = GROUP_LABELS.get(group, group)
    linear = route.get("linear", "yes")
    symbol_desc = route.get("symbol_description", "")
    itinerary = route.get("itinerary", [])

    ref_str = f" [{ref}]" if ref else ""
    type_str = "Rundweg" if linear == "no" else "Strecke"
    symbol_str = f" | Markierung: {symbol_desc}" if symbol_desc else ""
    itin_str = f" | {' → '.join(itinerary)}" if itinerary else ""

    return (
        f"- **{name}**{ref_str} ({group_label}, {type_str})\n"
        f"  ID: {rid}{symbol_str}{itin_str}"
    )


def _format_route_detail(data: dict, activity: str) -> str:
    """Format detailed route information."""
    name = data.get("name", "Unbenannt")
    ref = data.get("ref", "")
    rid = data.get("id", "?")
    group = data.get("group", "")
    group_label = GROUP_LABELS.get(group, group)

    route_info = data.get("route", {})
    length_m = route_info.get("length", 0) if isinstance(route_info, dict) else 0
    length_km = length_m / 1000
    linear = data.get("linear", route_info.get("linear", "yes") if isinstance(route_info, dict) else "yes")

    official_length = data.get("official_length")
    if official_length:
        official_km = official_length / 1000
        length_str = f"{official_km:.0f} km (offiziell)"
    elif length_km > 0:
        length_str = f"{length_km:.1f} km"
    else:
        length_str = "unbekannt"

    url = data.get("url", "")
    operator = data.get("operator", "")
    description = data.get("description", "")
    note = data.get("note", "")
    symbol_desc = data.get("symbol_description", "")

    tags = data.get("tags", {})
    ascent = tags.get("ascent", "")
    descent = tags.get("descent", "")

    lines = [f"# {name}"]
    if ref:
        lines.append(f"**Ref:** {ref}")
    lines.append(f"**Netzwerk:** {group_label}")
    lines.append(f"**Typ:** {'Rundweg' if linear == 'no' else 'Strecke'}")
    lines.append(f"**Länge:** {length_str}")

    if ascent:
        lines.append(f"**Aufstieg:** {ascent}")
    if descent:
        lines.append(f"**Abstieg:** {descent}")
    if symbol_desc:
        lines.append(f"**Markierung:** {symbol_desc}")
    if operator:
        lines.append(f"**Betreiber:** {operator}")
    if description:
        lines.append(f"\n{description}")
    if note:
        lines.append(f"\n📝 {note}")
    if url:
        lines.append(f"\n🔗 {url}")

    # Subroutes
    subroutes = data.get("subroutes", {})
    if subroutes:
        lines.append(f"\n## Teilstrecken ({len(subroutes)})")
        for sr in list(subroutes.values())[:10]:
            sr_name = sr.get("name", "?")
            sr_ref = sr.get("ref", "")
            sr_id = sr.get("id", "?")
            ref_part = f" [{sr_ref}]" if sr_ref else ""
            lines.append(f"- {sr_name}{ref_part} (ID: {sr_id})")

    # Superroutes
    superroutes = data.get("superroutes", {})
    if superroutes:
        lines.append(f"\n## Teil von")
        for sr in superroutes.values():
            sr_name = sr.get("name", "?")
            sr_id = sr.get("id", "?")
            lines.append(f"- {sr_name} (ID: {sr_id})")

    lines.append(f"\nQuelle: https://{activity}.waymarkedtrails.org/#route?id={rid}")
    lines.append(f"OSM: https://www.openstreetmap.org/relation/{rid}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_routes(
    query: str,
    activity: str = "hiking",
    limit: int = 10,
) -> str:
    """Search for marked hiking or cycling routes by name.

    Searches the Waymarked Trails database (based on OpenStreetMap data)
    for officially marked recreational routes.

    Args:
        query: Search query — route name, region, or keyword.
               Examples: "Spreewald", "Rund um Berlin", "Jakobsweg"
        activity: Type of route — "hiking" or "cycling"
        limit: Maximum number of results (1-20)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"
    if activity not in VALID_ACTIVITIES:
        return f"Error: activity must be one of {VALID_ACTIVITIES}"
    if not (1 <= limit <= 20):
        return "Error: limit must be between 1 and 20"

    data = await _get_json(activity, f"/list/search?query={query.strip()}&limit={limit}")
    if isinstance(data, str):
        return data

    results = data.get("results", [])
    if not results:
        return f"Keine Routen gefunden für '{query}' ({activity})"

    emoji = "🥾" if activity == "hiking" else "🚴"
    lines = [f"{emoji} Gefunden: {len(results)} Route(n) für '{query}'\n"]
    for route in results:
        lines.append(_format_route_summary(route, activity))

    return "\n".join(lines)


@mcp.tool()
async def get_route_details(
    route_id: int,
    activity: str = "hiking",
) -> str:
    """Get detailed information about a specific route.

    Returns name, length, operator, description, markings, and sub-routes.
    Use search_routes first to find route IDs.

    Args:
        route_id: OSM relation ID of the route (from search_routes results)
        activity: Type of route — "hiking" or "cycling"
    """
    if not route_id or route_id < 1:
        return "Error: route_id must be a positive integer"
    if activity not in VALID_ACTIVITIES:
        return f"Error: activity must be one of {VALID_ACTIVITIES}"

    data = await _get_json(activity, f"/details/relation/{route_id}")
    if isinstance(data, str):
        return data

    return _format_route_detail(data, activity)


@mcp.tool()
async def search_routes_in_region(
    region: str,
    activity: str = "hiking",
    limit: int = 15,
) -> str:
    """Search for routes in a specific region or area.

    Convenience wrapper that searches by region name. For Berlin/Brandenburg
    cycling tours, try queries like "Brandenburg", "Havelland", "Märkische Schweiz".

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

    Returns the route structure including sub-routes and their connections.
    Useful for understanding which towns/places a route passes through.

    Args:
        route_id: OSM relation ID of the route
        activity: Type of route — "hiking" or "cycling"
    """
    if not route_id or route_id < 1:
        return "Error: route_id must be a positive integer"
    if activity not in VALID_ACTIVITIES:
        return f"Error: activity must be one of {VALID_ACTIVITIES}"

    data = await _get_json(activity, f"/details/relation/{route_id}")
    if isinstance(data, str):
        return data

    name = data.get("name", "Unbenannt")
    route_info = data.get("route", {})

    if not isinstance(route_info, dict):
        return f"Keine Routendaten verfügbar für '{name}'"

    length_m = route_info.get("length", 0)
    length_km = length_m / 1000
    linear = route_info.get("linear", "yes")

    lines = [
        f"# Routenverlauf: {name}",
        f"**Gesamtlänge:** {length_km:.1f} km",
        f"**Typ:** {'Rundweg' if linear == 'no' else 'Strecke'}",
    ]

    # Show subroutes as stages
    subroutes = data.get("subroutes", {})
    if subroutes:
        lines.append(f"\n## Etappen ({len(subroutes)})\n")
        for i, sr in enumerate(subroutes.values(), 1):
            sr_name = sr.get("name", "?")
            sr_ref = sr.get("ref", "")
            sr_id = sr.get("id", "?")
            sr_linear = sr.get("linear", "yes")
            ref_part = f" [{sr_ref}]" if sr_ref else ""
            type_part = "↺" if sr_linear == "no" else "→"
            lines.append(f"{i}. {type_part} {sr_name}{ref_part} (ID: {sr_id})")
    else:
        # No subroutes — show itinerary from tags if available
        tags = data.get("tags", {})
        # Check for itinerary in the search result
        itinerary = data.get("itinerary", [])
        if itinerary:
            lines.append(f"\n## Verlauf\n")
            lines.append(" → ".join(itinerary))

    lines.append(f"\nQuelle: https://{activity}.waymarkedtrails.org/#route?id={route_id}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
