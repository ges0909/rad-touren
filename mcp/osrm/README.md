# OSRM MCP Server

Car routing with GPX export via the public [OSRM](http://project-osrm.org/) demo server.

## Features

- **No API key required** — uses the public OSRM demo server
- **OSM-based** — accurate street routing with realistic drive times
- **GPX export** — full road geometry saved as GPX track
- **Station waypoints** — named waypoints embedded in GPX

## Tools

| Tool                  | Description                                              |
| --------------------- | -------------------------------------------------------- |
| `calculate_car_route` | Route summary with distance, duration, per-leg breakdown |
| `route_to_gpx`        | Calculate route and save as GPX file with full geometry  |

## Setup

```bash
cd mcp/osrm
uv sync
```

## Usage

```bash
fastmcp run server.py
```

## Notes

- The public OSRM server is for demo/development use. For production, self-host OSRM.
- Coordinate order: **[longitude, latitude]** (same as all other MCP servers in this project).
- Maximum 100 waypoints per request.
- Only `driving` profile available on the public server.
