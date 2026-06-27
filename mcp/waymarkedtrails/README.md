# Waymarked Trails MCP Server

MCP server for discovering marked hiking and cycling routes via the [Waymarked Trails](https://waymarkedtrails.org) API. All data comes from OpenStreetMap.

## Tools

| Tool                      | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| `search_routes`           | Search for routes by name or keyword                       |
| `get_route_details`       | Get detailed info (length, markings, operator, sub-routes) |
| `search_routes_in_region` | Search routes by region name                               |
| `get_route_segments`      | Get route structure and stages                             |

## Supported Activities

- `hiking` — Marked hiking trails (waymarkedtrails.org/hiking)
- `cycling` — Marked cycling routes (waymarkedtrails.org/cycling)

## Setup

```bash
cd mcp/waymarkedtrails
uv sync
```

## Run

```bash
uv run fastmcp run server.py
```

## Usage Examples

Search for hiking routes:

```
search_routes("Märkische Schweiz", activity="hiking")
search_routes("Jakobsweg", activity="hiking")
```

Search for cycling routes in a region:

```
search_routes("Brandenburg", activity="cycling")
search_routes("Havelland", activity="cycling")
```

Get route details:

```
get_route_details(12365714, activity="cycling")  # Rund um Berlin
get_route_details(1624750, activity="hiking")    # Naturparkroute Märkische Schweiz
```

## API

Uses the public [Waymarked Trails API](https://github.com/waymarkedtrails/waymarkedtrails-api):

- `https://hiking.waymarkedtrails.org/api/v1/`
- `https://cycling.waymarkedtrails.org/api/v1/`

No API key required. Data licensed under ODbL (OpenStreetMap).
