"""MCP server wrapping the Open-Meteo API for weather forecasts and geocoding.

Uses lib.weather for all API logic. This file provides MCP tool declarations
and formats raw JSON results into human-readable strings.
"""

from fastmcp import FastMCP

from lib.weather import weather_forecast as _forecast, geocoding as _geocoding

mcp = FastMCP("Open-Meteo Weather")

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
    lines.append(f"Location: {data.get('latitude')}°N, {data.get('longitude')}°E")
    lines.append(f"Elevation: {data.get('elevation')}m")
    lines.append(f"Timezone: {data.get('timezone')} ({data.get('timezone_abbreviation')})")
    lines.append("")

    if "current" in data:
        c = data["current"]
        units = data.get("current_units", {})
        lines.append("## Current Conditions")
        for key, val in c.items():
            if key in ("time", "interval"):
                continue
            elif key == "weather_code":
                lines.append(f"  Weather: {WEATHER_CODES.get(val, val)}")
            else:
                lines.append(f"  {key}: {val}{units.get(key, '')}")
        lines.append("")

    if "daily" in data:
        d = data["daily"]
        units = data.get("daily_units", {})
        lines.append("## Daily Forecast")
        for i, date in enumerate(d.get("time", [])):
            lines.append(f"\n### {date}")
            for key, values in d.items():
                if key == "time":
                    continue
                val = values[i] if i < len(values) else "?"
                if key == "weather_code":
                    lines.append(f"  Weather: {WEATHER_CODES.get(val, val)}")
                else:
                    lines.append(f"  {key}: {val}{units.get(key, '')}")
        lines.append("")

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
                if key == "weather_code":
                    parts.append(f"weather={WEATHER_CODES.get(val, val)}")
                else:
                    parts.append(f"{key}={val}{units.get(key, '')}")
            lines.append("  " + " | ".join(parts))
        if len(times) > 24:
            lines.append(f"  ... ({len(times) - 24} more hours)")
        lines.append("")

    return "\n".join(lines)


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

    try:
        data = await _forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
            daily=daily,
            hourly=hourly,
            current=current,
            timezone=timezone,
            past_days=past_days,
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
            precipitation_unit=precipitation_unit,
        )
    except Exception as e:
        return f"Error: {e}"

    return _format_forecast(data)


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

    try:
        data = await _geocoding(name, count, language)
    except Exception as e:
        return f"Error: {e}"

    results = data.get("results", [])
    if not results:
        return f"No locations found for '{name}'"

    lines = [f"Found {len(results)} location(s):\n"]
    for r in results:
        lines.append(
            f"- {r.get('name', '?')}"
            f" ({r.get('admin1', '')}, {r.get('country', '')})"
            f" — lat: {r.get('latitude')}, lon: {r.get('longitude')}"
            f", elevation: {r.get('elevation', '?')}m"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
