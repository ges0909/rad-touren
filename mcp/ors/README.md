# OpenRouteService MCP Server

MCP server for car, bike, and foot routing via [OpenRouteService](https://openrouteservice.org/).

## Tools

| Tool              | Purpose                                                         |
| ----------------- | --------------------------------------------------------------- |
| `calculate_route` | Route between 2–50 waypoints with distance/duration per segment |
| `geocode`         | Geocode place names to coordinates (with country filter)        |
| `driving_time`    | Quick distance/duration between two points                      |
| `isochrone`       | Calculate reachability areas from a location (time-based)       |
| `distance_matrix` | Driving times/distances between all pairs of locations (N×N)    |

## Profiles

- `driving-car` — Car routing (default)
- `driving-hgv` — Heavy goods vehicle
- `cycling-regular` — Standard cycling
- `cycling-road` — Road cycling
- `cycling-mountain` — Mountain biking
- `foot-walking` — Walking
- `foot-hiking` — Hiking

## Setup

1. Register at [openrouteservice.org/dev/#/signup](https://openrouteservice.org/dev/#/signup)
2. Create a token → get API key
3. Set environment variable: `ORS_API_KEY=your-key`

## Rate Limits

- Free tier: 2,000 requests/day, 40 requests/minute
- No credit card required
