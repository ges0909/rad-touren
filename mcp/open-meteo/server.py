"""MCP server wrapping the Open-Meteo API for weather forecasts and geocoding."""

from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Open-Meteo Weather")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.open-meteo.com/v1"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

HOURLY_VARIABLES = [
    "temperature_2m", "relative_humidity_2m", "dewpoint_2m",
    "apparent_temperature", "precipitation_probability", "precipitation",
    "rain", "showers", "snowfall", "snow_depth", "weather_code",
    "pressure_msl", "surface_pressure", "cloud_cover", "cloud_cover_low",
    "cloud_cover_mid", "cloud_cover_high", "visibility",
    "wind_speed_10m", "wind_speed_80m", "wind_direction_10m",
    "wind_direction_80m", "wind_gusts_10m", "uv_index", "is_day",
    "sunshine_duration",
]

DAILY_VARIABLES = [
    "weather_code", "temperature_2m_max", "temperature_2m_min",
    "apparent_temperature_max", "apparent_temperature_min",
    "sunrise", "sunset", "daylight_duration", "sunshine_duration",
    "uv_index_max", "precipitation_sum", "rain_sum", "showers_sum",
    "snowfall_sum", "precipitation_hours", "precipitation_probability_max",
    "wind_speed_10m_max", "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
]

CURRENT_VARIABLES = [
    "temperature_2m", "relative_humidity_2m", "apparent_temperature",
    "precipitation", "rain", "showers", "snowfall", "weather_code",
    "cloud_cover", "wind_speed_10m", "wind_direction_10m",
    "wind_gusts_10m", "is_day",
]


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

async def _get_json(url: str, params: dict) -> dict | str:
    """Make GET request and return JSON or error string."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params)
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
async def weather_forecast(
    latitude: float,
    longitude: float,
    hourly: list[str] | None = None,
    daily: list[str] | None = None,
    current: list[str] | None = None,
    timezone: str = "auto",
    forecast_days: int = 7,
    past_days: int = 0,
    temperature_unit: str = "celsius",
    wind_speed_unit: str = "kmh",
    precipitation_unit: str = "mm",
) -> str:
    """Get weather forecast for given coordinates using Open-Meteo API.

    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        hourly: List of hourly variables (e.g. temperature_2m, precipitation)
        daily: List of daily variables (e.g. temperature_2m_max, precipitation_sum)
        current: List of current condition variables
        timezone: Timezone (e.g. Europe/Berlin, auto)
        forecast_days: Number of forecast days (1-16)
        past_days: Include past days (0-92)
        temperature_unit: celsius or fahrenheit
        wind_speed_unit: kmh, ms, mph, or kn
        precipitation_unit: mm or inch
    """
    if not (-90 <= latitude <= 90):
        return "Error: latitude must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return "Error: longitude must be between -180 and 180"
    if not (1 <= forecast_days <= 16):
        return "Error: forecast_days must be between 1 and 16"

    params: dict = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": forecast_days,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "precipitation_unit": precipitation_unit,
    }

    if past_days > 0:
        params["past_days"] = past_days
    if hourly:
        params["hourly"] = ",".join(hourly)
    if daily:
        params["daily"] = ",".join(daily)
    if current:
        params["current"] = ",".join(current)

    # Need at least one data group
    if not hourly and not daily and not current:
        params["daily"] = ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "precipitation_probability_max",
            "wind_speed_10m_max", "wind_direction_10m_dominant",
        ])

    result = await _get_json(f"{BASE_URL}/forecast", params)
    if isinstance(result, str):
        return result

    return _format_forecast(result)


@mcp.tool()
async def geocoding(
    name: str,
    count: int = 5,
    language: str = "en",
) -> str:
    """Search for locations by name. Returns coordinates and location details.

    Args:
        name: Place name to search for (min 2 characters)
        count: Number of results (1-100)
        language: Language for results (e.g. en, de)
    """
    if len(name) < 2:
        return "Error: name must be at least 2 characters"
    if not (1 <= count <= 100):
        return "Error: count must be between 1 and 100"

    params = {"name": name, "count": count, "language": language, "format": "json"}
    result = await _get_json(GEOCODING_URL, params)
    if isinstance(result, str):
        return result

    results = result.get("results", [])
    if not results:
        return f"No locations found for '{name}'"

    lines = [f"Found {len(results)} location(s):\n"]
    for r in results:
        line = (
            f"- {r.get('name', '?')}"
            f" ({r.get('admin1', '')}, {r.get('country', '')})"
            f" — lat: {r.get('latitude')}, lon: {r.get('longitude')}"
            f", elevation: {r.get('elevation', '?')}m"
        )
        lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
    82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _format_forecast(data: dict) -> str:
    """Format Open-Meteo JSON response into readable text."""
    lines = []

    # Metadata
    lines.append(f"Location: {data.get('latitude')}°N, {data.get('longitude')}°E")
    lines.append(f"Elevation: {data.get('elevation')}m")
    lines.append(f"Timezone: {data.get('timezone')} ({data.get('timezone_abbreviation')})")
    lines.append("")

    # Current conditions
    if "current" in data:
        c = data["current"]
        lines.append("## Current Conditions")
        units = data.get("current_units", {})
        for key, val in c.items():
            if key == "time":
                lines.append(f"  Time: {val}")
            elif key == "interval":
                continue
            elif key == "weather_code":
                lines.append(f"  Weather: {WEATHER_CODES.get(val, val)}")
            else:
                unit = units.get(key, "")
                lines.append(f"  {key}: {val}{unit}")
        lines.append("")

    # Daily forecast
    if "daily" in data:
        d = data["daily"]
        units = data.get("daily_units", {})
        times = d.get("time", [])
        lines.append("## Daily Forecast")
        for i, date in enumerate(times):
            lines.append(f"\n### {date}")
            for key, values in d.items():
                if key == "time":
                    continue
                val = values[i] if i < len(values) else "?"
                unit = units.get(key, "")
                if key == "weather_code":
                    lines.append(f"  Weather: {WEATHER_CODES.get(val, val)}")
                else:
                    lines.append(f"  {key}: {val}{unit}")
        lines.append("")

    # Hourly forecast (summarized — first 24h)
    if "hourly" in data:
        h = data["hourly"]
        units = data.get("hourly_units", {})
        times = h.get("time", [])
        lines.append("## Hourly Forecast (next 24h)")
        for i, t in enumerate(times[:24]):
            parts = [f"{t}:"]
            for key, values in h.items():
                if key == "time":
                    continue
                val = values[i] if i < len(values) else "?"
                unit = units.get(key, "")
                if key == "weather_code":
                    parts.append(f"weather={WEATHER_CODES.get(val, val)}")
                else:
                    parts.append(f"{key}={val}{unit}")
            lines.append("  " + " | ".join(parts))
        if len(times) > 24:
            lines.append(f"  ... ({len(times) - 24} more hours)")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
