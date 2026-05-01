"""Tests for open-meteo-mcp server."""

import pytest
import respx
import httpx

from server import weather_forecast, geocoding, _format_forecast, WEATHER_CODES


@respx.mock
@pytest.mark.asyncio
async def test_weather_forecast_basic():
    """Test basic forecast request."""
    mock_response = {
        "latitude": 52.52,
        "longitude": 13.41,
        "elevation": 38.0,
        "timezone": "Europe/Berlin",
        "timezone_abbreviation": "CEST",
        "daily": {
            "time": ["2026-05-01"],
            "temperature_2m_max": [22.0],
            "temperature_2m_min": [10.0],
            "weather_code": [1],
        },
        "daily_units": {
            "time": "iso8601",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "weather_code": "wmo code",
        },
    }
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await weather_forecast(latitude=52.52, longitude=13.41, daily=["temperature_2m_max"])
    assert "52.52" in result
    assert "22.0" in result


@respx.mock
@pytest.mark.asyncio
async def test_weather_forecast_invalid_latitude():
    """Test validation of latitude."""
    result = await weather_forecast(latitude=100, longitude=13.41)
    assert "Error" in result


@respx.mock
@pytest.mark.asyncio
async def test_weather_forecast_invalid_longitude():
    """Test validation of longitude."""
    result = await weather_forecast(latitude=52.0, longitude=200)
    assert "Error" in result


@respx.mock
@pytest.mark.asyncio
async def test_weather_forecast_http_error():
    """Test handling of HTTP errors."""
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(400, text="Bad request")
    )
    result = await weather_forecast(latitude=52.52, longitude=13.41)
    assert "HTTP error" in result or "Error" in result


@respx.mock
@pytest.mark.asyncio
async def test_geocoding_basic():
    """Test basic geocoding."""
    mock_response = {
        "results": [
            {
                "name": "Berlin",
                "latitude": 52.52,
                "longitude": 13.41,
                "country": "Germany",
                "admin1": "Berlin",
                "elevation": 38.0,
            }
        ]
    }
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await geocoding(name="Berlin")
    assert "Berlin" in result
    assert "52.52" in result


@respx.mock
@pytest.mark.asyncio
async def test_geocoding_no_results():
    """Test geocoding with no results."""
    respx.get("https://geocoding-api.open-meteo.com/v1/search").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    result = await geocoding(name="xyznonexistent")
    assert "No locations found" in result


@pytest.mark.asyncio
async def test_geocoding_short_query():
    """Test geocoding with too short query."""
    result = await geocoding(name="x")
    assert "Error" in result


def test_format_forecast_with_current():
    """Test formatting with current conditions."""
    data = {
        "latitude": 52.52,
        "longitude": 13.41,
        "elevation": 38.0,
        "timezone": "Europe/Berlin",
        "timezone_abbreviation": "CEST",
        "current": {
            "time": "2026-05-01T12:00",
            "temperature_2m": 20.5,
            "weather_code": 1,
        },
        "current_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "weather_code": "wmo code",
        },
    }
    result = _format_forecast(data)
    assert "Current Conditions" in result
    assert "Mainly clear" in result
    assert "20.5" in result


def test_weather_codes():
    """Test weather code mapping."""
    assert WEATHER_CODES[0] == "Clear sky"
    assert WEATHER_CODES[95] == "Thunderstorm"
