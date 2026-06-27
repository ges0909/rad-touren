# open-meteo-mcp

MCP server wrapping the [Open-Meteo API](https://open-meteo.com/) for weather forecasts and geocoding. No API key required.

## Tools

| Tool               | Description                                                   |
| ------------------ | ------------------------------------------------------------- |
| `weather_forecast` | Get weather forecast (hourly, daily, current) for coordinates |
| `geocoding`        | Search for locations by name, returns coordinates             |

## Setup

```json
{
  "open-meteo": {
    "command": "uv",
    "args": ["run", "--directory", "mcp/open-meteo", "python", "server.py"]
  }
}
```

## API

Uses the free [Open-Meteo API](https://open-meteo.com/en/docs) — no registration, no API key, no rate limits for non-commercial use.

## Tests

```bash
uv run --directory mcp/open-meteo pytest -v
```
