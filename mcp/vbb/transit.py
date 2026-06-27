"""VBB public transit client — stop search, departures, journey planning."""

from typing import Any

import httpx

BASE_URL = "https://v6.vbb.transport.rest"
TIMEOUT = 30


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
    """Make GET request to VBB REST API."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}{path}", params=params or {})
        resp.raise_for_status()
        return resp.json()


async def search_stops(query: str, results: int = 10) -> dict[str, Any]:
    """Search for public transport stops by name.

    Args:
        query: Stop name query.
        results: Max results (1-50).
    """
    params = {
        "query": query.strip(),
        "results": results,
        "stops": "true",
        "addresses": "false",
        "poi": "false",
    }

    data = await _get("/locations", params)

    if not data:
        return {"error": f"No stops found for '{query}'"}

    stops: list[dict[str, Any]] = []
    for stop in data if isinstance(data, list) else []:
        if stop.get("type") != "stop":
            continue
        loc = stop.get("location", {})
        products = stop.get("products", {})
        stops.append(
            {
                "id": stop.get("id", "?"),
                "name": stop.get("name", "?"),
                "lat": loc.get("latitude"),
                "lon": loc.get("longitude"),
                "products": [k for k, v in products.items() if v],
            }
        )

    return {"stops": stops}


async def get_departures(stop_id: str, results: int = 10, duration: int = 60) -> dict[str, Any]:
    """Get upcoming departures from a stop.

    Args:
        stop_id: Stop ID from search_stops.
        results: Number of departures (1-50).
        duration: Time window in minutes (1-360).
    """
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

    data = await _get(f"/stops/{stop_id}/departures", params)
    departures_list = data if isinstance(data, list) else data.get("departures", [])

    departures: list[dict[str, Any]] = []
    for dep in departures_list[:results]:
        departures.append(
            {
                "line": dep.get("line", {}).get("name", "?"),
                "direction": dep.get("direction", "?"),
                "when": dep.get("plannedWhen", dep.get("when", "?")),
                "delay_sec": dep.get("delay"),
                "platform": dep.get("platform", ""),
                "cancelled": dep.get("cancelled", False),
            }
        )

    return {"departures": departures}


async def get_journeys(
    origin: str, destination: str, departure: str | None = None, results: int = 3
) -> dict[str, Any]:
    """Plan a journey between two stops.

    Args:
        origin: Origin stop ID.
        destination: Destination stop ID.
        departure: Departure time (ISO 8601 or natural language).
        results: Number of journey options (1-6).
    """
    params: dict[str, Any] = {
        "from": origin,
        "to": destination,
        "results": results,
        "stopovers": "true",
        "tickets": "true",
    }
    if departure:
        params["departure"] = departure

    data = await _get("/journeys", params)
    journeys_data = data.get("journeys", []) if isinstance(data, dict) else []

    journeys: list[dict[str, Any]] = []
    for j in journeys_data:
        legs: list[dict[str, Any]] = []
        for leg in j.get("legs", []):
            legs.append(
                {
                    "origin": leg.get("origin", {}).get("name", "?"),
                    "destination": leg.get("destination", {}).get("name", "?"),
                    "line": leg.get("line", {}).get("name") if leg.get("line") else None,
                    "departure": leg.get("plannedDeparture", leg.get("departure")),
                    "arrival": leg.get("plannedArrival", leg.get("arrival")),
                    "walking": leg.get("walking", False),
                }
            )

        # Extract ticket prices
        tickets: list[dict[str, Any]] = []
        for ticket_group in j.get("price", {}).get("tickets", j.get("tickets", [])):
            if isinstance(ticket_group, dict):
                name = ticket_group.get("name", "")
                price = ticket_group.get("price", {})
                amount = price.get("amount")
                if amount is not None:
                    tickets.append({"name": name, "amount_cents": amount})

        journeys.append({"legs": legs, "tickets": tickets})

    return {"journeys": journeys}
