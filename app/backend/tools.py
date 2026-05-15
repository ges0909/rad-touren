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

# Type alias
type ToolFn = Any

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
]

# Map tool name → async function
TOOL_REGISTRY: dict[str, ToolFn] = {
    "geocode": geocode,
    "driving_time": driving_time,
    "weather_forecast": weather_forecast,
    "search_routes": search_routes,
    "calculate_car_route": calculate_car_route,
}
