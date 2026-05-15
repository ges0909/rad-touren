"""MCP server wrapping the VBB REST API for Berlin/Brandenburg public transport.

Uses lib.transit for all API logic. This file provides MCP tool declarations
and formats structured results into human-readable strings.
"""

from fastmcp import FastMCP

from lib.transit import search_stops as _search_stops, get_departures as _get_departures, get_journeys as _get_journeys

mcp = FastMCP("VBB Public Transport")


@mcp.tool()
async def search_stops(query: str, results: int = 10) -> str:
    """Search for public transport stops by name.

    Args:
        query: Search query for stop names (e.g. "Alexanderplatz", "Strausberg Nord")
        results: Maximum number of results to return (1-50)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"

    result = await _search_stops(query.strip(), results)

    if "error" in result:
        return result["error"]

    stops = result["stops"]
    lines = [f"Found {len(stops)} stop(s):\n"]
    for s in stops:
        products_str = ", ".join(s["products"]) if s["products"] else "—"
        lines.append(
            f"- **{s['name']}** (ID: {s['id']})\n"
            f"  lat: {s['lat']}, lon: {s['lon']}\n"
            f"  Products: {products_str}"
        )

    return "\n".join(lines)


@mcp.tool()
async def get_departures(stop_id: str, results: int = 10, duration: int = 60) -> str:
    """Get upcoming departures from a stop.

    Args:
        stop_id: Stop ID (from search_stops)
        results: Number of departures to return (1-50)
        duration: Time window in minutes (1-360)
    """
    if not stop_id:
        return "Error: stop_id is required"

    result = await _get_departures(stop_id, results, duration)

    if "error" in result:
        return result["error"]

    departures = result["departures"]
    if not departures:
        return f"No departures found for stop {stop_id}"

    lines = [f"Departures from stop {stop_id}:\n"]
    for dep in departures:
        when = dep["when"]
        time_str = when[11:16] if when and len(when) > 16 else when
        delay_str = f" (+{dep['delay_sec'] // 60} min)" if dep.get("delay_sec") and dep["delay_sec"] > 0 else ""
        plat_str = f" [Gl. {dep['platform']}]" if dep["platform"] else ""
        cancel_str = " ❌ FÄLLT AUS" if dep["cancelled"] else ""
        lines.append(f"- {time_str}{delay_str} {dep['line']} → {dep['direction']}{plat_str}{cancel_str}")

    return "\n".join(lines)


@mcp.tool()
async def get_journeys(
    origin: str,
    destination: str,
    departure: str | None = None,
    results: int = 3,
) -> str:
    """Plan a journey between two stops.

    Args:
        origin: Origin stop ID (from search_stops)
        destination: Destination stop ID (from search_stops)
        departure: Departure time (ISO 8601 or natural language like "tomorrow 8am").
                   If omitted, uses current time.
        results: Number of journey options (1-6)
    """
    if not origin:
        return "Error: origin stop ID is required"
    if not destination:
        return "Error: destination stop ID is required"

    result = await _get_journeys(origin, destination, departure, results)

    if "error" in result:
        return result["error"]

    journeys = result["journeys"]
    if not journeys:
        return f"No journeys found from {origin} to {destination}"

    lines = [f"Found {len(journeys)} journey(s):\n"]
    for i, journey in enumerate(journeys, 1):
        legs = journey["legs"]
        if not legs:
            continue

        dep_str = legs[0]["departure"][11:16] if legs[0].get("departure") else "?"
        arr_str = legs[-1]["arrival"][11:16] if legs[-1].get("arrival") else "?"
        transfers = sum(1 for leg in legs if leg.get("line") and not leg.get("walking")) - 1
        transfers = max(0, transfers)

        lines.append(f"### Journey {i}: {dep_str} → {arr_str} ({transfers} transfer{'s' if transfers != 1 else ''})")

        for leg in legs:
            if leg.get("walking"):
                lines.append("  🚶 Walk")
                continue
            line_name = leg.get("line", "?")
            lines.append(f"  **{line_name}**: {leg['origin']} → {leg['destination']}")

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
