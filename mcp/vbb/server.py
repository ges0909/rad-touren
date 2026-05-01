"""MCP server wrapping the VBB REST API for Berlin/Brandenburg public transport."""

import httpx
from fastmcp import FastMCP

mcp = FastMCP("VBB Public Transport")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://v6.vbb.transport.rest"


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

async def _get_json(path: str, params: dict | None = None) -> dict | list | str:
    """Make GET request to VBB REST API and return JSON or error string."""
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params or {})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error {e.response.status_code}: {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_stops(query: str, results: int = 10) -> str:
    """Search for public transport stops by name.

    Args:
        query: Search query for stop names (e.g. "Alexanderplatz", "Strausberg Nord")
        results: Maximum number of results to return (1-50)
    """
    if not query or len(query.strip()) < 2:
        return "Error: query must be at least 2 characters"
    if not (1 <= results <= 50):
        return "Error: results must be between 1 and 50"

    params = {
        "query": query.strip(),
        "results": results,
        "stops": "true",
        "addresses": "false",
        "poi": "false",
    }

    data = await _get_json("/locations", params)
    if isinstance(data, str):
        return data

    if not data:
        return f"No stops found for '{query}'"

    lines = [f"Found {len(data)} stop(s):\n"]
    for stop in data:
        if stop.get("type") != "stop":
            continue
        stop_id = stop.get("id", "?")
        name = stop.get("name", "?")
        loc = stop.get("location", {})
        lat = loc.get("latitude", "?")
        lon = loc.get("longitude", "?")
        products = stop.get("products", {})
        transport = [k for k, v in products.items() if v]

        lines.append(
            f"- **{name}** (ID: {stop_id})\n"
            f"  lat: {lat}, lon: {lon}\n"
            f"  Products: {', '.join(transport)}"
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
    if not (1 <= results <= 50):
        return "Error: results must be between 1 and 50"
    if not (1 <= duration <= 360):
        return "Error: duration must be between 1 and 360"

    params = {
        "results": results,
        "duration": duration,
        "suburban": "true",
        "subway": "true",
        "tram": "true",
        "bus": "true",
        "ferry": "true",
        "express": "true",
        "regional": "true",
    }

    data = await _get_json(f"/stops/{stop_id}/departures", params)
    if isinstance(data, str):
        return data

    departures = data if isinstance(data, list) else data.get("departures", [])
    if not departures:
        return f"No departures found for stop {stop_id}"

    lines = [f"Departures from stop {stop_id}:\n"]
    for dep in departures[:results]:
        line_name = dep.get("line", {}).get("name", "?")
        direction = dep.get("direction", "?")
        planned = dep.get("plannedWhen", dep.get("when", "?"))
        delay = dep.get("delay")
        platform = dep.get("platform", "")

        time_str = planned[11:16] if planned and len(planned) > 16 else planned
        delay_str = ""
        if delay and delay > 0:
            delay_str = f" (+{delay // 60} min)"

        plat_str = f" [Gl. {platform}]" if platform else ""
        lines.append(f"- {time_str}{delay_str} {line_name} → {direction}{plat_str}")

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
    if not (1 <= results <= 6):
        return "Error: results must be between 1 and 6"

    params: dict = {
        "from": origin,
        "to": destination,
        "results": results,
        "suburban": "true",
        "subway": "true",
        "tram": "true",
        "bus": "true",
        "ferry": "true",
        "express": "true",
        "regional": "true",
        "bicycle": "true",
    }

    if departure:
        params["departure"] = departure

    data = await _get_json("/journeys", params)
    if isinstance(data, str):
        return data

    journeys = data.get("journeys", []) if isinstance(data, dict) else []
    if not journeys:
        return f"No journeys found from {origin} to {destination}"

    lines = [f"Found {len(journeys)} journey(s):\n"]
    for i, journey in enumerate(journeys, 1):
        legs = journey.get("legs", [])
        if not legs:
            continue

        # Journey summary
        dep_time = legs[0].get("plannedDeparture", legs[0].get("departure", "?"))
        arr_time = legs[-1].get("plannedArrival", legs[-1].get("arrival", "?"))
        dep_str = dep_time[11:16] if dep_time and len(dep_time) > 16 else dep_time
        arr_str = arr_time[11:16] if arr_time and len(arr_time) > 16 else arr_time

        transfers = sum(1 for leg in legs if not leg.get("walking") and leg.get("line")) - 1
        transfers = max(0, transfers)

        lines.append(f"### Journey {i}: {dep_str} → {arr_str} ({transfers} transfer{'s' if transfers != 1 else ''})")

        for leg in legs:
            if leg.get("walking"):
                dist = leg.get("distance", "")
                dist_str = f" ({dist}m)" if dist else ""
                lines.append(f"  🚶 Walk{dist_str}")
                continue

            line_info = leg.get("line", {})
            line_name = line_info.get("name", "?")
            product = line_info.get("product", "")
            direction = leg.get("direction", "?")
            origin_name = leg.get("origin", {}).get("name", "?")
            dest_name = leg.get("destination", {}).get("name", "?")
            leg_dep = leg.get("plannedDeparture", leg.get("departure", "?"))
            leg_arr = leg.get("plannedArrival", leg.get("arrival", "?"))
            leg_dep_str = leg_dep[11:16] if leg_dep and len(leg_dep) > 16 else leg_dep
            leg_arr_str = leg_arr[11:16] if leg_arr and len(leg_arr) > 16 else leg_arr

            platform_dep = leg.get("departurePlatform", "")
            platform_arr = leg.get("arrivalPlatform", "")
            plat_str = f" [Gl. {platform_dep}→{platform_arr}]" if platform_dep else ""

            # Check bicycle
            remarks = leg.get("remarks", [])
            bike = any("bicycle" in (r.get("text", "") + r.get("code", "")).lower()
                      for r in remarks if isinstance(r, dict))
            bike_str = " 🚲" if bike else ""

            lines.append(
                f"  {leg_dep_str}–{leg_arr_str} "
                f"**{line_name}** → {direction}{plat_str}{bike_str}\n"
                f"    {origin_name} → {dest_name}"
            )

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
