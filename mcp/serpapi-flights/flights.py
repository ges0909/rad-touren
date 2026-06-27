"""Pure HTTP client logic for SerpAPI Google Flights.

No FastMCP dependency — importable independently for testing.
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
SERPAPI_BASE_URL = "https://serpapi.com/search.json"

# Travel class mapping: human-readable → SerpAPI value
TRAVEL_CLASS_MAP = {
    "economy": "1",
    "premium_economy": "2",
    "business": "3",
    "first": "4",
}


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
    currency: str = "EUR",
    language: str = "de",
) -> dict:
    """Search for flights via SerpAPI Google Flights.

    Returns raw API response as dict, or {"error": "..."} on failure.
    """
    if not SERPAPI_API_KEY:
        return {"error": "SERPAPI_API_KEY not configured"}

    travel_class_code = TRAVEL_CLASS_MAP.get(travel_class.lower(), "1")
    trip_type = 1 if return_date else 2  # 1=round trip, 2=one-way

    params: dict = {
        "engine": "google_flights",
        "departure_id": fly_from.upper(),
        "arrival_id": fly_to.upper(),
        "outbound_date": outbound_date,
        "travel_class": travel_class_code,
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
        "currency": currency.upper(),
        "hl": language,
        "type": trip_type,
        "api_key": SERPAPI_API_KEY,
    }

    if return_date:
        params["return_date"] = return_date

    if stops is not None:
        params["stops"] = stops

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(SERPAPI_BASE_URL, params=params)
    except httpx.TimeoutException:
        return {"error": "Request timed out — SerpAPI did not respond in time"}

    if response.status_code == 401:
        return {"error": "Invalid SERPAPI_API_KEY"}
    if response.status_code == 429:
        return {"error": "SerpAPI rate limit reached (100 searches/month on free plan)"}
    if response.status_code != 200:
        return {"error": f"SerpAPI returned HTTP {response.status_code}"}

    data = response.json()

    if "error" in data:
        return {"error": f"SerpAPI: {data['error']}"}

    return data


async def search_airport(query: str, language: str = "de") -> dict:
    """Search for airports via SerpAPI Google Flights autocomplete.

    Returns raw API response as dict, or {"error": "..."} on failure.
    """
    if not SERPAPI_API_KEY:
        return {"error": "SERPAPI_API_KEY not configured"}

    params = {
        "engine": "google_flights_autocomplete",
        "q": query,
        "hl": language,
        "api_key": SERPAPI_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(SERPAPI_BASE_URL, params=params)
    except httpx.TimeoutException:
        return {"error": "Request timed out"}

    if response.status_code != 200:
        return {"error": f"SerpAPI returned HTTP {response.status_code}"}

    data = response.json()

    if "error" in data:
        return {"error": f"SerpAPI: {data['error']}"}

    return data
