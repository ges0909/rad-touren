"""MCP server for flight search using SerpAPI Google Flights.

Provides tools for searching flights and looking up airport codes.
Requires SERPAPI_API_KEY environment variable (free tier: 100 searches/month).
Register at https://serpapi.com/users/sign_up

Usage:
    python server.py
"""

from fastmcp import FastMCP
from flights import search_airport as _search_airport
from flights import search_flights as _search_flights

mcp = FastMCP("SerpAPI Flight Search")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_flight_option(option: dict, currency: str) -> str:
    """Format a single flight option (one itinerary) into readable text."""
    lines = []

    price = option.get("price", "?")
    total_min = option.get("total_duration", 0)
    total_h, total_m = divmod(total_min, 60)
    flight_type = option.get("type", "")

    lines.append(f"**{price} {currency}** — {total_h}h {total_m}min gesamt ({flight_type})")

    # Individual flight legs
    for leg in option.get("flights", []):
        dep = leg.get("departure_airport", {})
        arr = leg.get("arrival_airport", {})
        airline = leg.get("airline", "?")
        flight_no = leg.get("flight_number", "")
        duration = leg.get("duration", 0)
        leg_h, leg_m = divmod(duration, 60)
        travel_class = leg.get("travel_class", "")
        airplane = leg.get("airplane", "")

        dep_time = dep.get("time", "?")[11:16] if dep.get("time") else "?"
        arr_time = arr.get("time", "?")[11:16] if arr.get("time") else "?"
        dep_date = dep.get("time", "")[:10] if dep.get("time") else ""

        overnight = " 🌙" if leg.get("overnight") else ""
        delayed = " ⚠️ oft verspätet" if leg.get("often_delayed_by_over_30_min") else ""

        lines.append(
            f"  ✈️ {dep.get('id', '?')} {dep_time} → {arr.get('id', '?')} {arr_time}"
            f"  ({leg_h}h {leg_m}min){overnight}{delayed}"
        )
        lines.append(
            f"     {airline} {flight_no} · {airplane} · {travel_class}"
            + (f" · {dep_date}" if dep_date else "")
        )

    # Layovers
    layovers = option.get("layovers", [])
    if layovers:
        layover_parts = []
        for lv in layovers:
            lv_h, lv_m = divmod(lv.get("duration", 0), 60)
            overnight = " (overnight)" if lv.get("overnight") else ""
            layover_parts.append(f"{lv.get('id', '?')} {lv_h}h {lv_m}min{overnight}")
        lines.append(f"  🔄 Stopover: {' → '.join(layover_parts)}")

    # Carbon emissions
    carbon = option.get("carbon_emissions", {})
    if carbon:
        kg = carbon.get("this_flight", 0) // 1000
        diff = carbon.get("difference_percent", 0)
        diff_str = f"+{diff}%" if diff > 0 else f"{diff}%"
        lines.append(f"  🌱 CO₂: ~{kg} kg ({diff_str} vs. Durchschnitt)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_flights(
    fly_from: str,
    fly_to: str,
    outbound_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    travel_class: str = "economy",
    stops: int | None = None,
    max_results: int = 5,
    currency: str = "EUR",
    language: str = "de",
) -> str:
    """Search for flights using Google Flights via SerpAPI.

    Returns real flight options with prices, times, airlines and booking links.
    Uses Google Flights data — covers virtually all routes worldwide.

    Args:
        fly_from: Origin airport IATA code (e.g. "BER", "FRA", "MUC")
        fly_to: Destination airport IATA code (e.g. "BIO", "BCN", "PMI")
            Use comma-separated codes for multi-airport cities: "LON" or "LHR,LGW"
        outbound_date: Departure date in YYYY-MM-DD format (e.g. "2026-09-04")
        return_date: Return date in YYYY-MM-DD format — omit for one-way flights
        adults: Number of adult passengers (default: 1)
        children: Number of children aged 2-11 (default: 0)
        infants_in_seat: Number of infants with own seat (default: 0)
        infants_on_lap: Number of lap infants under 2 (default: 0)
        travel_class: economy, premium_economy, business, or first (default: economy)
        stops: Max number of stops — 0 for direct only, 1 for max 1 stop, None for any (default: any)
        max_results: Maximum number of options to show (default: 5)
        currency: Currency code for prices (default: EUR)
        language: Language for results, e.g. "de" or "en" (default: de)
    """
    data = await _search_flights(
        fly_from=fly_from,
        fly_to=fly_to,
        outbound_date=outbound_date,
        return_date=return_date,
        adults=adults,
        children=children,
        infants_in_seat=infants_in_seat,
        infants_on_lap=infants_on_lap,
        travel_class=travel_class,
        stops=stops,
        currency=currency,
        language=language,
    )

    if "error" in data:
        return f"Error: {data['error']}"

    best = data.get("best_flights", [])
    other = data.get("other_flights", [])
    all_flights = best + other

    if not all_flights:
        trip_desc = f"{fly_from.upper()} → {fly_to.upper()} am {outbound_date}"
        return (
            f"Keine Flüge gefunden für {trip_desc}.\n"
            f"Tipp: Prüfe die Flughafencodes mit search_airport()."
        )

    # Limit results
    shown = all_flights[:max_results]

    # Header
    trip_label = "Hin- & Rückflug" if return_date else "Hinflug"
    date_label = outbound_date + (f" → {return_date}" if return_date else "")
    pax_parts = [f"{adults} Erw."]
    if children:
        pax_parts.append(f"{children} Kinder")
    if infants_in_seat or infants_on_lap:
        pax_parts.append(f"{infants_in_seat + infants_on_lap} Kleinkinder")

    lines = [
        f"## ✈️ {trip_label}: {fly_from.upper()} → {fly_to.upper()}",
        f"📅 {date_label} · 👥 {', '.join(pax_parts)} · 💺 {travel_class.capitalize()}",
        f"Zeige {len(shown)} von {len(all_flights)} Optionen:\n",
    ]

    for i, option in enumerate(shown, 1):
        marker = "⭐ " if i <= len(best) else ""
        lines.append(f"### Option {i} {marker}")
        lines.append(_format_flight_option(option, currency.upper()))
        lines.append("")

    if len(best) > 0:
        lines.append("_⭐ = von Google als beste Option eingestuft_")

    return "\n".join(lines)


@mcp.tool()
async def search_airport(
    query: str,
    language: str = "de",
) -> str:
    """Search for airports and cities to find IATA codes for flight search.

    Use this before search_flights if you're unsure about the correct airport code.

    Args:
        query: City name, airport name, or partial IATA code
               Examples: "Bilbao", "Berlin", "BER", "Palma de Mallorca"
        language: Language for results, e.g. "de" or "en" (default: de)
    """
    data = await _search_airport(query, language)

    if "error" in data:
        return f"Error: {data['error']}"

    airports = data.get("airports", [])
    if not airports:
        return f"Keine Flughäfen gefunden für '{query}'"

    lines = [f"Flughäfen für '{query}':\n"]
    for group in airports:
        city = group.get("city", "")
        if city:
            lines.append(f"**{city}**")
        for airport in group.get("airports", [group]):
            code = airport.get("id", airport.get("code", "?"))
            name = airport.get("name", "?")
            country = airport.get("country", "")
            lines.append(f"  - **{code}** — {name}" + (f" ({country})" if country else ""))

    lines.append("\nDen Code (z.B. BER, BIO) als fly_from/fly_to in search_flights verwenden.")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
