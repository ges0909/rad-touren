# vbb-mcp

MCP server wrapping the [VBB REST API](https://v6.vbb.transport.rest/) for Berlin/Brandenburg public transport. No API key required.

## Tools

| Tool             | Description                         |
| ---------------- | ----------------------------------- |
| `search_stops`   | Search for stops by name            |
| `get_departures` | Get upcoming departures from a stop |
| `get_journeys`   | Plan a journey between two stops    |

## Setup

```json
{
  "vbb": {
    "command": "uv",
    "args": ["run", "--directory", "mcp/vbb", "python", "server.py"]
  }
}
```

## API

Uses the free [VBB REST API](https://v6.vbb.transport.rest/) by [@derhuerst](https://github.com/derhuerst/vbb-rest) — no registration, no API key. Rate limit: 100 req/min.

## Tests

```bash
uv run --directory mcp/vbb pytest -v
```
