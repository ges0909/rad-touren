"""Open-Meteo weather forecast client."""

from typing import Any

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
TIMEOUT = 30


async def weather_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 7,
    daily: list[str] | None = None,
    hourly: list[str] | None = None,
    current: list[str] | None = None,
    timezone: str = "auto",
    past_days: int = 0,
    temperature_unit: str = "celsius",
    wind_speed_unit: str = "kmh",
    precipitation_unit: str = "mm",
) -> dict[str, Any]:
    """Get weather forecast via Open-Meteo.

    Args:
        latitude: Latitude (-90 to 90).
        longitude: Longitude (-180 to 180).
        forecast_days: Number of forecast days (1-16).
        daily: List of daily variables.
        hourly: List of hourly variables.
        current: List of current condition variables.
        timezone: Timezone string.
        past_days: Include past days (0-92).
        temperature_unit: celsius or fahrenheit.
        wind_speed_unit: kmh, ms, mph, or kn.
        precipitation_unit: mm or inch.
    """
    params: dict[str, Any] = {
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

    # Default to daily if nothing specified
    if not hourly and not daily and not current:
        params["daily"] = (
            "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"
        )

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{OPEN_METEO_URL}/forecast", params=params)
        resp.raise_for_status()
        return resp.json()


async def geocoding(name: str, count: int = 5, language: str = "en") -> dict[str, Any]:
    """Search for locations by name via Open-Meteo geocoding.

    Args:
        name: Place name (min 2 chars).
        count: Number of results (1-100).
        language: Language for results.
    """
    params = {"name": name, "count": count, "language": language, "format": "json"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(GEOCODING_URL, params=params)
        resp.raise_for_status()
        return resp.json()
