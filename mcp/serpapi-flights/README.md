# SerpAPI Flight Search MCP Server

Flight search via [Google Flights](https://www.google.com/flights) using the
[SerpAPI](https://serpapi.com/google-flights-api). Returns real-time prices,
schedules, and booking links for virtually all routes worldwide.

## Setup

1. Register at [serpapi.com](https://serpapi.com/users/sign_up) (free: 100 searches/month)
2. Copy your API key from the dashboard
3. Set the environment variable: `SERPAPI_API_KEY=your-key`

## Tools

### `search_flights`

Search for flights between two airports.

```python
search_flights(
    fly_from="BER",
    fly_to="BIO",
    outbound_date="2026-09-04",
    return_date="2026-09-20",
    adults=2,
    travel_class="economy",
    stops=0,          # 0 = direct only, None = any
    currency="EUR",
)
```

Parameters:

| Parameter         | Type | Default  | Description                                       |
| ----------------- | ---- | -------- | ------------------------------------------------- |
| `fly_from`        | str  | required | Origin IATA code (e.g. `BER`)                     |
| `fly_to`          | str  | required | Destination IATA code (e.g. `BIO`)                |
| `outbound_date`   | str  | required | Departure date `YYYY-MM-DD`                       |
| `return_date`     | str  | None     | Return date — omit for one-way                    |
| `adults`          | int  | 1        | Adult passengers                                  |
| `children`        | int  | 0        | Children aged 2–11                                |
| `infants_in_seat` | int  | 0        | Infants with own seat                             |
| `infants_on_lap`  | int  | 0        | Lap infants under 2                               |
| `travel_class`    | str  | economy  | `economy`, `premium_economy`, `business`, `first` |
| `stops`           | int  | None     | `0` = direct only, `1` = max 1 stop, `None` = any |
| `max_results`     | int  | 5        | Max options to return                             |
| `currency`        | str  | EUR      | Currency code                                     |
| `language`        | str  | de       | Result language (`de`, `en`, …)                   |

### `search_airport`

Look up IATA codes for airports and cities.

```python
search_airport("Bilbao")
# → BIO — Bilbao Airport (Spain)

search_airport("Berlin")
# → BER — Berlin Brandenburg Airport
# → TXL — Berlin Tegel (closed)
```

## API Details

- Base URL: `https://serpapi.com/search.json`
- Engine: `google_flights` / `google_flights_autocomplete`
- Auth: API key via `api_key` query parameter
- Free tier: **100 searches/month** — sufficient for personal use
- Paid plans from $75/month (5,000 searches)
- Data source: Google Flights (real-time, all routes)

## Running

```bash
cd mcp/serpapi-flights
uv run python server.py
```

Or via MCP config (see `.kiro/settings/mcp.json`).
