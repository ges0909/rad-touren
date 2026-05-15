"""Tool declarations and registry for the Gemini agent.

All API logic lives in lib/ — this file only wires tools to Gemini declarations.
"""

from typing import Any

from lib.geocoding import geocode
from lib.routing import calculate_car_route
from lib.weather import weather_forecast
from lib.routes import search_routes
from lib.brouter import calculate_route as _calculate_bike_route, search_location
from lib.transit import search_stops, get_departures, get_journeys
from lib.wikivoyage import search_destinations, get_article, search_nearby

# Type alias
type ToolFn = Any


async def calculate_bike_route(waypoints: list[list[float]], profile: str = "trekking") -> dict[str, Any]:
    """Wrapper that extracts geometry from GPX and strips raw content."""
    result = await _calculate_bike_route(waypoints=waypoints, profile=profile)
    if "error" in result:
        return result

    # Extract (lat, lon) geometry from GPX content for map display
    # BRouter uses <trkpt lon="..." lat="..."> (lon first!)
    content = result.pop("content", "")
    geometry: list[tuple[float, float]] = []
    if content:
        import re
        for match in re.finditer(r'<trkpt\s+lon="([^"]+)"\s+lat="([^"]+)"', content):
            geometry.append((float(match.group(2)), float(match.group(1))))  # (lat, lon)

    result["geometry"] = geometry
    result["waypoints"] = [[wp[1], wp[0]] for wp in waypoints]  # [lat, lon]
    return result

# ---------------------------------------------------------------------------
# Gemini Function Declarations
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "geocode",
        "description": "Geocode a place name to [longitude, latitude] coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Place name or address"},
                "country": {"type": "string", "description": "ISO 3166-1 alpha-2 country code (optional)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "weather_forecast",
        "description": "Get weather forecast for given coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "forecast_days": {"type": "integer", "description": "Number of days (1-16)"},
            },
            "required": ["latitude", "longitude"],
        },
    },
    {
        "name": "search_routes",
        "description": "Search for marked hiking or cycling routes by name or region.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Route name, region, or keyword"},
                "activity": {"type": "string", "enum": ["hiking", "cycling"]},
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculate_car_route",
        "description": "Calculate a car route between waypoints. Returns distance (km), duration (min), and full route geometry for map display. Use this for ALL driving distance calculations — it replaces driving_time and also shows the route on the map.",
        "parameters": {
            "type": "object",
            "properties": {
                "waypoints": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                    "description": "List of [longitude, latitude] pairs (min 2)",
                },
            },
            "required": ["waypoints"],
        },
    },
    {
        "name": "calculate_bike_route",
        "description": "Calculate a cycling route between waypoints via BRouter. Returns distance, elevation, and route geometry for map display. ALWAYS use this when planning a bike tour to show the route on the map.",
        "parameters": {
            "type": "object",
            "properties": {
                "waypoints": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                    "description": "List of [longitude, latitude] pairs (min 2)",
                },
                "profile": {
                    "type": "string",
                    "description": "Routing profile: trekking, fastbike, safety, shortest",
                },
            },
            "required": ["waypoints"],
        },
    },
    {
        "name": "search_location",
        "description": "Search for a location by name via Nominatim. Returns coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Place name or address"},
                "country_code": {"type": "string", "description": "ISO country code (default: de)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_stops",
        "description": "Search for public transport stops by name (Berlin/Brandenburg VBB).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Stop name query"},
                "results": {"type": "integer", "description": "Max results (1-50)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_departures",
        "description": "Get upcoming departures from a public transport stop.",
        "parameters": {
            "type": "object",
            "properties": {
                "stop_id": {"type": "string", "description": "Stop ID from search_stops"},
                "results": {"type": "integer", "description": "Number of departures (1-50)"},
                "duration": {"type": "integer", "description": "Time window in minutes (1-360)"},
            },
            "required": ["stop_id"],
        },
    },
    {
        "name": "get_journeys",
        "description": "Plan a journey between two public transport stops.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Origin stop ID"},
                "destination": {"type": "string", "description": "Destination stop ID"},
                "departure": {"type": "string", "description": "Departure time (ISO 8601 or natural language)"},
                "results": {"type": "integer", "description": "Number of journey options (1-6)"},
            },
            "required": ["origin", "destination"],
        },
    },
    {
        "name": "search_destinations",
        "description": "Search for travel destinations on Wikivoyage.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Destination name, region, or keyword"},
                "lang": {"type": "string", "enum": ["de", "en"], "description": "Language edition"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_article",
        "description": "Get a full Wikivoyage travel guide article for a destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Exact article title"},
                "lang": {"type": "string", "enum": ["de", "en"], "description": "Language edition"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "search_nearby",
        "description": "Find Wikivoyage articles about places near given coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius": {"type": "integer", "description": "Search radius in meters (max 10000)"},
                "lang": {"type": "string", "enum": ["de", "en"]},
            },
            "required": ["lat", "lon"],
        },
    },
]

# Map tool name → async function
TOOL_REGISTRY: dict[str, ToolFn] = {
    "geocode": geocode,
    "weather_forecast": weather_forecast,
    "search_routes": search_routes,
    "calculate_car_route": calculate_car_route,
    "calculate_bike_route": calculate_bike_route,
    "search_location": search_location,
    "search_stops": search_stops,
    "get_departures": get_departures,
    "get_journeys": get_journeys,
    "search_destinations": search_destinations,
    "get_article": get_article,
    "search_nearby": search_nearby,
}
