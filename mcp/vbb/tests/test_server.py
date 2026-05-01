"""Tests for vbb-mcp server."""

import pytest
import respx
import httpx

from server import search_stops, get_departures, get_journeys


BASE = "https://v6.vbb.transport.rest"


@respx.mock
@pytest.mark.asyncio
async def test_search_stops_basic():
    """Test basic stop search."""
    mock_response = [
        {
            "type": "stop",
            "id": "900100003",
            "name": "S+U Alexanderplatz",
            "location": {"latitude": 52.521508, "longitude": 13.411267},
            "products": {"suburban": True, "subway": True, "tram": True, "bus": True},
        }
    ]
    respx.get(f"{BASE}/locations").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await search_stops("Alexanderplatz")
    assert "Alexanderplatz" in result
    assert "900100003" in result


@pytest.mark.asyncio
async def test_search_stops_short_query():
    """Test validation of short query."""
    result = await search_stops("x")
    assert "Error" in result


@respx.mock
@pytest.mark.asyncio
async def test_search_stops_no_results():
    """Test empty results."""
    respx.get(f"{BASE}/locations").mock(
        return_value=httpx.Response(200, json=[])
    )
    result = await search_stops("xyznonexistent")
    assert "No stops found" in result


@respx.mock
@pytest.mark.asyncio
async def test_get_departures_basic():
    """Test basic departures."""
    mock_response = [
        {
            "line": {"name": "S5", "product": "suburban"},
            "direction": "S Westkreuz",
            "plannedWhen": "2026-05-03T10:15:00+02:00",
            "delay": 120,
            "platform": "2",
        },
        {
            "line": {"name": "RB24", "product": "regional"},
            "direction": "Eberswalde Hbf",
            "plannedWhen": "2026-05-03T10:22:00+02:00",
            "delay": None,
            "platform": "3",
        },
    ]
    respx.get(f"{BASE}/stops/900320001/departures").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await get_departures("900320001")
    assert "S5" in result
    assert "Westkreuz" in result
    assert "+2 min" in result
    assert "RB24" in result


@pytest.mark.asyncio
async def test_get_departures_no_stop_id():
    """Test missing stop ID."""
    result = await get_departures("")
    assert "Error" in result


@respx.mock
@pytest.mark.asyncio
async def test_get_journeys_basic():
    """Test basic journey planning."""
    mock_response = {
        "journeys": [
            {
                "legs": [
                    {
                        "origin": {"name": "S Blankenfelde (TF) Bhf"},
                        "destination": {"name": "S+U Lichtenberg Bhf"},
                        "line": {"name": "RB24", "product": "regional"},
                        "direction": "Eberswalde Hbf",
                        "plannedDeparture": "2026-05-03T10:09:00+02:00",
                        "plannedArrival": "2026-05-03T10:45:00+02:00",
                        "departurePlatform": "2",
                        "arrivalPlatform": "16",
                        "remarks": [
                            {"type": "hint", "code": "FK", "text": "Bicycle conveyance"}
                        ],
                    },
                    {
                        "origin": {"name": "S+U Lichtenberg Bhf"},
                        "destination": {"name": "S Strausberg Nord"},
                        "line": {"name": "S5", "product": "suburban"},
                        "direction": "S Strausberg Nord",
                        "plannedDeparture": "2026-05-03T11:01:00+02:00",
                        "plannedArrival": "2026-05-03T11:45:00+02:00",
                        "departurePlatform": "1",
                        "arrivalPlatform": "2",
                        "remarks": [
                            {"type": "hint", "code": "FK", "text": "Bicycle conveyance"}
                        ],
                    },
                ]
            }
        ]
    }
    respx.get(f"{BASE}/journeys").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await get_journeys("900245027", "900320001")
    assert "RB24" in result
    assert "S5" in result
    assert "Strausberg" in result
    assert "Journey 1" in result


@pytest.mark.asyncio
async def test_get_journeys_missing_origin():
    """Test missing origin."""
    result = await get_journeys("", "900320001")
    assert "Error" in result


@respx.mock
@pytest.mark.asyncio
async def test_get_journeys_no_results():
    """Test no journeys found."""
    respx.get(f"{BASE}/journeys").mock(
        return_value=httpx.Response(200, json={"journeys": []})
    )
    result = await get_journeys("900000001", "900000002")
    assert "No journeys found" in result


@respx.mock
@pytest.mark.asyncio
async def test_get_journeys_with_walking():
    """Test journey with walking leg."""
    mock_response = {
        "journeys": [
            {
                "legs": [
                    {
                        "walking": True,
                        "distance": 150,
                        "origin": {"name": "Start"},
                        "destination": {"name": "Stop A"},
                        "plannedDeparture": "2026-05-03T10:00:00+02:00",
                        "plannedArrival": "2026-05-03T10:03:00+02:00",
                    },
                    {
                        "origin": {"name": "Stop A"},
                        "destination": {"name": "Stop B"},
                        "line": {"name": "U2", "product": "subway"},
                        "direction": "Pankow",
                        "plannedDeparture": "2026-05-03T10:05:00+02:00",
                        "plannedArrival": "2026-05-03T10:20:00+02:00",
                        "departurePlatform": "",
                        "arrivalPlatform": "",
                        "remarks": [],
                    },
                ]
            }
        ]
    }
    respx.get(f"{BASE}/journeys").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    result = await get_journeys("900000001", "900000002")
    assert "Walk" in result
    assert "150m" in result
    assert "U2" in result
