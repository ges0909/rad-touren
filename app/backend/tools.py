"""Tool declarations and registry for the Gemini agent.

All API logic lives in lib/ — this file only wires tools to Gemini declarations.
"""

import sys
from pathlib import Path
from typing import Any

# Add lib/ to path for shared imports
LIB_DIR = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR.parent))

from lib.geocoding import geocode
from lib.routing import calculate_car_route, driving_time
from lib.weather import weather_forecast
from lib.routes import search_routes
from lib.brouter import calculate_route as _calculate_bike_route, search_location
from lib.transit import search_stops, get_departures, get_journeys
from lib.wikivoyage import search_destinations, get_article, search_nearby

# Type alias
type ToolFn = Any


async def calculate_bike_route(waypoints: list[list[float]], profile: str = "trekking") -> dict[str, Any]:
    """Wrapper that strips GPX content to keep Gemini context small."""
    result = await _calculate_bike_route(waypoints=waypoints, profile=profile)
    result.pop("content", None)  # Remove large GPX body
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
        "name": "driving_time",
        "description": "Get driving time and distance between two points. Coordinates as [longitude, latitude].",
        "parameters": {
            "type": "object",
            "properties": {
                "from_coords": {"type": "array", "items": {"type": "number"}, "description": "[longitude, latitude]"},
                "to_coords": {"type": "array", "items": {"type": "number"}, "description": "[longitude, latitude]"},
            },
            "required": ["from_coords", "to_coords"],
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
        "description": "Calculate a car route between waypoints. Returns distance, duration, and geometry.",
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
        "description": "Calculate a cycling route between waypoints via BRouter. Returns GPX content.",
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
    "driving_time": driving_time,
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
