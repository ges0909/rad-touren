# 🚲 Cycling Tours Berlin/Brandenburg

Day trip cycling tours in the Berlin/Brandenburg region — planned and generated with [Kiro](https://kiro.dev) using custom MCP servers for routing, weather, and public transit.

All tours are round trips reachable by regional train from Blankenfelde-Mahlow. Tour descriptions are in German.

**→ [Tour catalog](cycling/README.md)**

## Project Structure

```
├── cycling/                 # Cycling tour descriptions, GPX tracks, map images
├── hiking/                  # Hiking tour descriptions (planned)
├── roadtrips/               # Multi-day car trips in Europe (planned)
├── mcp/                     # Custom MCP servers (all Python/FastMCP)
│   ├── brouter/             # Cycling routing, geocoding, map rendering
│   ├── open-meteo/          # Weather forecast
│   ├── overpass/            # POI search along routes (OpenStreetMap)
│   └── vbb/                 # Berlin/Brandenburg public transport
└── .kiro/
    ├── settings/mcp.json    # MCP server configuration
    └── steering/            # AI steering rules for tour planning
```

## Steering

The [steering file](.kiro/steering/cycling-tour-planning.md) is what turns Kiro from a general-purpose assistant into a cycling tour planner. It encodes:

- **Workflow** — 10-step sequence: geocode → route → GPX → map → weather → transit → events → markdown → index → summary
- **Template** — consistent markdown structure, emoji conventions, POI categories
- **Constraints** — geographic bounds, coordinate conventions, round-trip rules
- **Transit rules** — home station, API verification before claiming connections
- **Lifecycle** — which sections are stable (GPX, map) vs. date-dependent (weather, events, transit)

A single prompt like _"Plan a 50 km tour through the Spreewald"_ produces a complete tour document with route map, elevation profile, verified transit connections, and current weather. To adapt this project to your own region, change the home station and geographic bounds in the steering file.

## MCP Servers

| Server                                   | Purpose                           | API                                                                              |
| ---------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------- |
| [`brouter`](mcp/brouter/README.md)       | Routing, geocoding, map rendering | [BRouter](https://brouter.de) + [Nominatim](https://nominatim.openstreetmap.org) |
| [`open-meteo`](mcp/open-meteo/README.md) | Weather forecast + geocoding      | [Open-Meteo](https://open-meteo.com/)                                            |
| [`vbb`](mcp/vbb/README.md)               | Stop search, departures, journeys | [VBB REST](https://v6.vbb.transport.rest/)                                       |
| [`overpass`](mcp/overpass/README.md)     | POI search along routes           | [Overpass](https://overpass-api.de/) (OpenStreetMap)                             |

All four are custom Python servers (FastMCP + httpx). No API keys, no Node.js.

## Why Custom Servers?

The project started with third-party MCP servers: [openroute-mcp](https://pypi.org/project/openroute-mcp/) for routing, [open-meteo-mcp-server](https://www.npmjs.com/package/open-meteo-mcp-server) (npm) for weather, and [berlin-transport-mcp](https://github.com/harshil1712/berlin-transport-mcp) (remote SSE) for transit. I replaced all three for these reasons:

- **Routing quality** — OpenRouteService had waypoint snapping failures in rural Brandenburg, poor geocoding, and no cycling route specialization. BRouter follows designated cycle routes (EuroVelo, national routes) and handles rural areas gracefully.
- **Runtime consistency** — the weather and transit servers required Node.js/npm alongside Python, creating a mixed stack with two package managers.
- **Reliability** — the transit server ran on a third-party hosting platform (`mcp-tools.app`). The weather server was an unmaintained community npm package. Both could break without notice.
- **Control** — all underlying APIs are free and keyless, so wrapping them directly in Python removes unnecessary intermediaries.

## Setup

Requires [Kiro](https://kiro.dev) and [uv](https://docs.astral.sh/uv/getting-started/installation/). Servers are configured in `.kiro/settings/mcp.json` and connect automatically on startup:

```json
{
  "mcpServers": {
    "brouter": {
      "command": "uv",
      "args": ["run", "--directory", "mcp/brouter", "python", "server.py"]
    },
    "open-meteo": {
      "command": "uv",
      "args": ["run", "--directory", "mcp/open-meteo", "python", "server.py"]
    },
    "vbb": {
      "command": "uv",
      "args": ["run", "--directory", "mcp/vbb", "python", "server.py"]
    },
    "overpass": {
      "command": "uv",
      "args": ["run", "--directory", "mcp/overpass", "python", "server.py"]
    }
  }
}
```

## Hooks

Agent hooks automate consistency checks. When a GPX file is modified, the **GPX Consistency Check** hook triggers and ensures:

1. Route map is re-rendered (with POI markers)
2. Elevation profile is re-rendered
3. Distance in the tour markdown is updated
4. Tour catalog index is updated if distance changed

This prevents GPX, map images, and markdown from drifting out of sync after route edits or spur removal.

## Tests

```bash
uv run --directory mcp/brouter pytest -v
uv run --directory mcp/open-meteo pytest -v
uv run --directory mcp/vbb pytest -v
uv run --directory mcp/overpass pytest -v
```

## License

Route data: © [BRouter](https://brouter.de) / [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. Map tiles: © OpenStreetMap contributors. Geocoding: [Nominatim](https://nominatim.openstreetmap.org).
