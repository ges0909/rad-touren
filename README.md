# 🚲 Cycling Tours Berlin/Brandenburg

Day trip cycling tours in the Berlin/Brandenburg region — planned and generated with [Kiro](https://kiro.dev) using MCP servers for routing, weather, and public transit.

All tours are **round trips** (start = finish) reachable by regional train from Blankenfelde-Mahlow. Tour descriptions are in German; this README provides the project overview in English.

**→ [Tour catalog (German)](touren/README.md)**

## Why a Custom BRouter MCP Server?

This project initially used the [openroute-mcp](https://pypi.org/project/openroute-mcp/) server for routing via the [OpenRouteService API](https://openrouteservice.org/). While functional, it had recurring issues:

- **Waypoint snapping failures** — the API returned 404 errors when waypoints couldn't be snapped to the road network, especially in rural areas and near water
- **Poor geocoding in Brandenburg** — location search often returned results outside Germany
- **API key requirement** — OpenRouteService requires a free API key, adding setup friction
- **No cycling specialization** — generic routing that doesn't follow designated long-distance cycling routes

To solve these problems, we built a custom MCP server (`brouter-mcp/`) that wraps the [BRouter](https://brouter.de) cycling routing engine and [Nominatim](https://nominatim.openstreetmap.org) geocoding API. BRouter is purpose-built for cycling: it follows long-distance cycle routes (EuroVelo, national routes), handles waypoint snapping more gracefully, includes elevation awareness, and requires no API key. The server also includes a `render_gpx_map` tool that generates static map images from GPX tracks using OpenStreetMap tiles — something the OpenRouteService MCP didn't offer.

See [brouter-mcp/README.md](brouter-mcp/README.md) for the server documentation.

## Project Structure

```
├── touren/                  # Tour descriptions, GPX tracks, map images (German)
│   ├── *.md                 # Individual tour descriptions
│   ├── gpx/                 # GPX tracks (BRouter trekking profile)
│   └── img/                 # Route map images (auto-generated PNGs)
├── brouter-mcp/             # Custom BRouter MCP server (Python)
│   ├── server.py            # Single-file FastMCP server
│   ├── tests/               # Property-based, unit, and integration tests
│   └── pyproject.toml       # Dependencies: fastmcp, httpx, staticmap, gpxpy
└── .kiro/
    ├── settings/mcp.json    # MCP server configuration
    ├── specs/               # Spec-driven development documents
    └── steering/            # AI steering rules for tour planning
```

## Setup

### Prerequisites

- [Kiro IDE](https://kiro.dev)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Node.js / npm (for weather and transit MCP servers)

### Install and configure

```bash
cd brouter-mcp && uv sync
```

The MCP servers are configured in `.kiro/settings/mcp.json`. Kiro connects to them automatically on startup.

### MCP Servers

| Server                                                                       | Purpose                                   | API Key |
| ---------------------------------------------------------------------------- | ----------------------------------------- | ------- |
| `brouter-mcp` (custom)                                                       | Cycling routing, geocoding, map rendering | ❌ None |
| [open-meteo-mcp-server](https://www.npmjs.com/package/open-meteo-mcp-server) | Weather forecast                          | ❌ None |
| [berlin-transport](https://berlin-transport.mcp-tools.app)                   | Public transit (S-Bahn, regional trains)  | ❌ None |

No API keys required — all services are free and open.

## Creating a New Tour

Ask Kiro in natural language, e.g.:

> _"Plan a 50 km round trip cycling tour from Potsdam for next Saturday"_

Kiro will:

1. Geocode waypoints and calculate the route via BRouter
2. Generate a GPX track with elevation data
3. Render a route map as PNG
4. Check the weather forecast
5. Look up public transit connections from Blankenfelde-Mahlow
6. Find points of interest, swimming spots, and cafés along the route
7. Write a markdown tour description with embedded map

## Running Tests

```bash
cd brouter-mcp && uv run pytest -v
```

34 tests: property-based validation (Hypothesis), unit tests, integration tests (respx), and GPX rendering.

## License

- Route data: © [BRouter](https://brouter.de) / [OpenStreetMap](https://www.openstreetmap.org/copyright) Contributors
- Map tiles: © [OpenStreetMap](https://www.openstreetmap.org/copyright) Contributors
- Geocoding: [Nominatim](https://nominatim.openstreetmap.org) (OpenStreetMap data)
