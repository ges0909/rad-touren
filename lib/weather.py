"""Open-Meteo weather forecast client."""

from typing import Any

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1"
TIMEOUT = 30


async def weather_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 7,
    daily: list[str] | None = None,
) -> dict[str, Any]:
    """Get weather forecast via Open-Meteo.

    Args:
        latitude: Latitude (-90 to 90).
        longitude: Longitude (-180 to 180).
        forecast_days: Number of forecast days (1-16).
        daily: List of daily variables. Defaults to temp, precipitation, wind.
    """
    if daily is None:
        daily = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"]

    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(daily),
        "timezone": "auto",
        "forecast_days": forecast_days,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{OPEN_METEO_URL}/forecast", params=params)
        resp.raise_for_status()
        data = resp.json()

    daily_data = data.get("daily", {})
    days: list[dict[str, Any]] = []
    for i, date in enumerate(daily_data.get("time", [])):
        day: dict[str, Any] = {"date": date}
        for key in daily:
            values = daily_data.get(key, [])
            day[key] = values[i] if i < len(values) else None
        days.append(day)

    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "days": days,
    }
