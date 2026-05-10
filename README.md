# 🗺️ Tour Planning — Cycling, Hiking & Roadtrips

AI-powered tour planning with [Kiro](https://kiro.dev) using custom MCP servers for routing, weather, POIs, and public transit.

- **Cycling** — Day trips in Berlin/Brandenburg, round trips by regional train
- **Hiking** — Day hikes in Berlin/Brandenburg (planned)
- **Roadtrips** — Multi-day car rental trips across Europe

All tour descriptions are in German.

**→ [Cycling tours](cycling/README.md)** · **[Roadtrips](roadtrips/README.md)**

## Project Structure

```
├── cycling/                 # Cycling tours: GPX tracks, maps, markdown
├── hiking/                  # Hiking tours (planned)
├── roadtrips/               # Multi-day car trips in Europe
├── mcp/                     # Custom MCP servers (all Python/FastMCP)
│   ├── brouter/             # Cycling/hiking routing, geocoding, map rendering
│   ├── ors/                 # Car/bike/foot routing via OpenRouteService
│   ├── open-meteo/          # Weather forecast
│   ├── overpass/            # POI search along routes (OpenStreetMap)
│   └── vbb/                 # Berlin/Brandenburg public transport
├── docs/                    # Concept documents
└── .kiro/
    ├── settings/mcp.json    # MCP server configuration
    ├── hooks/               # Agent hooks (GPX consistency check)
    └── steering/            # AI steering rules
        ├── user-preferences.md        # Shared interests & defaults (always loaded)
        ├── cycling-tour-planning.md   # Cycling workflow & template
        ├── roadtrip-planning.md       # Roadtrip workflow & template
        └── commit-messages.md         # Commit conventions
```

## Steering

Multiple steering files turn Kiro into a domain-specific tour planner:

| File                       | Scope          | Purpose                                                             |
| -------------------------- | -------------- | ------------------------------------------------------------------- |
| `user-preferences.md`      | Always         | Personal interests, food/accommodation rules, travel group defaults |
| `cycling-tour-planning.md` | `cycling/**`   | Cycling workflow, BRouter routing, VBB transit, fare tables         |
| `roadtrip-planning.md`     | `roadtrips/**` | Roadtrip workflow, ORS car routing, buffer rule, country info       |
| `commit-messages.md`       | Always         | Conventional Commits format                                         |

A single prompt like _"Plan a 50 km tour through the Spreewald"_ or _"Plan a 2-week roadtrip through Finland"_ produces a complete tour document with route, map, POIs, weather, and transport connections.

## MCP Servers

| Server                                   | Purpose                                              | API                                                                              | Used by         |
| ---------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------- | --------------- |
| [`brouter`](mcp/brouter/README.md)       | Cycling/hiking routing, geocoding, map rendering     | [BRouter](https://brouter.de) + [Nominatim](https://nominatim.openstreetmap.org) | Cycling, Hiking |
| [`ors`](mcp/ors/README.md)               | Car/bike/foot routing, geocoding, isochrones, matrix | [OpenRouteService](https://openrouteservice.org/)                                | Roadtrips       |
| [`open-meteo`](mcp/open-meteo/README.md) | Weather forecast + geocoding                         | [Open-Meteo](https://open-meteo.com/)                                            | All             |
| [`vbb`](mcp/vbb/README.md)               | Stop search, departures, journeys, fares             | [VBB REST](https://v6.vbb.transport.rest/)                                       | Cycling         |
| [`overpass`](mcp/overpass/README.md)     | POI search along routes                              | [Overpass](https://overpass-api.de/) (OpenStreetMap)                             | All             |

All five are custom Python servers (FastMCP + httpx). No Node.js.

### What doesn't need an MCP server

These are handled via `remote_web_search` because no free, stable API exists:

| Need                | Approach                           | Sources                           |
| ------------------- | ---------------------------------- | --------------------------------- |
| Flight search       | Web search for routes and prices   | Skyscanner, Google Flights, Kayak |
| Hotel/accommodation | Web search for recommendations     | Booking.com, Airbnb, travel blogs |
| Rental cars         | Web search for price comparison    | CHECK24, billiger-mietwagen.de    |
| Events & festivals  | Web search for current events      | visitberlin.de, local calendars   |
| S-Bahn disruptions  | Web search + fetch disruption page | sbahn.berlin                      |

## Hooks

Agent hooks automate consistency checks:

| Hook                  | Trigger                                    | Action                                                  |
| --------------------- | ------------------------------------------ | ------------------------------------------------------- |
| GPX Consistency Check | GPX file edited in `cycling/` or `hiking/` | Re-render map + elevation, update distances in markdown |

## Setup

Requires [Kiro](https://kiro.dev) and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Install all MCP server dependencies
uv sync --directory mcp/brouter
uv sync --directory mcp/ors
uv sync --directory mcp/open-meteo
uv sync --directory mcp/vbb
uv sync --directory mcp/overpass
```

Servers are configured in `.kiro/settings/mcp.json` and connect automatically on startup. The ORS server requires an API key (free at [openrouteservice.org](https://openrouteservice.org/dev/#/signup)).

## Tests

```bash
uv run --directory mcp/brouter pytest -v
uv run --directory mcp/open-meteo pytest -v
uv run --directory mcp/vbb pytest -v
uv run --directory mcp/overpass pytest -v
```

## License

Route data: © [BRouter](https://brouter.de) / [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. Map tiles: © OpenStreetMap / OpenTopoMap contributors. Geocoding: [Nominatim](https://nominatim.openstreetmap.org). Routing: [OpenRouteService](https://openrouteservice.org/).
