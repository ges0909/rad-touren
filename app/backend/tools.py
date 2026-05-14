"""Register MCP server functions as Gemini tool declarations."""

import sys
from pathlib import Path

# Add MCP server directories to path for direct import
MCP_DIR = Path(__file__).parent.parent.parent / "mcp"
for server_dir in MCP_DIR.iterdir():
    if server_dir.is_dir() and (server_dir / "server.py").exists():
        sys.path.insert(0, str(server_dir))


# --- Tool function implementations (thin wrappers around MCP servers) ---


async def geocode(query: str, country: str | None = None) -> dict:
    """Geocode a place name to coordinates."""
    sys.path.insert(0, str(MCP_DIR / "ors"))
    from server import geocode as ors_geocode
    return await ors_geocode(query=query, country=country)


async def driving_time(
    from_coords: list[float], to_coords: list[float]
) -> dict:
    """Get driving time and distance between two points."""
    sys.path.insert(0, str(MCP_DIR / "ors"))
    from server import driving_time as ors_driving_time
    return await ors_driving_time(from_coords=from_coords, to_coords=to_coords)


async def weather_forecast(
    latitude: float, longitude: float, forecast_days: int = 7
) -> dict:
    """Get weather forecast for coordinates."""
    sys.path.insert(0, str(MCP_DIR / "open-meteo"))
    from server import weather_forecast as meteo_forecast
    return await meteo_forecast(
        latitude=latitude, longitude=longitude, forecast_days=forecast_days,
        daily=["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
    )


async def search_routes(query: str, activity: str = "hiking") -> dict:
    """Search for marked hiking or cycling routes."""
    sys.path.insert(0, str(MCP_DIR / "waymarkedtrails"))
    from server import search_routes as wmt_search
    return await wmt_search(query=query, activity=activity)


async def calculate_car_route(waypoints: list[list[float]]) -> dict:
    """Calculate a car route between waypoints."""
    sys.path.insert(0, str(MCP_DIR / "osrm"))
    from server import calculate_car_route as osrm_route
    return await osrm_route(waypoints=waypoints)


# --- Gemini Function Declarations ---

TOOL_DECLARATIONS = [
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
        "description": "Calculate a car route between waypoints. Returns distance and duration.",
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
TOOL_REGISTRY = {
    "geocode": geocode,
    "driving_time": driving_time,
    "weather_forecast": weather_forecast,
    "search_routes": search_routes,
    "calculate_car_route": calculate_car_route,
}
