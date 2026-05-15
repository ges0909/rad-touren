# 🗺️ Tour Planning — Cycling, Hiking & Roadtrips

AI-powered tour planning with [Kiro](https://kiro.dev) and custom MCP servers for routing, weather, POIs, public transit, and travel guide content.

| Category     | Description                                         | Status  |
| ------------ | --------------------------------------------------- | ------- |
| 🚴 Cycling   | Day trips in Berlin/Brandenburg via regional trains | Active  |
| 🥾 Hiking    | Day hikes in Berlin/Brandenburg                     | Planned |
| 🚗 Roadtrips | Multi-day car rental trips across Europe            | Active  |

**→ [Cycling Tours](trips/bike/README.md)** · **→ [Roadtrips](trips/road/README.md)**

---

## Quickstart

Prerequisites: [Kiro](https://kiro.dev) + [uv](https://docs.astral.sh/uv/getting-started/installation/) + Node.js 20+ + npm

```bash
# Install all workspace packages (single command from project root)
uv sync --all-packages
```

```bash
# API keys (.env in project root, gitignored)
echo "ORS_API_KEY=your-key-here" >> .env
echo "GEMINI_API_KEY=your-key-here" >> .env
```

- OpenRouteService key (free): [openrouteservice.org](https://openrouteservice.org/dev/#/signup)
- Gemini API key (free): [Google AI Studio](https://aistudio.google.com)

All other MCP servers use free APIs without a key.

### Web App

The project includes a web-based trip planner (FastAPI + Vue 3 + Leaflet):

```bash
# Backend
cd app/backend && uv run uvicorn main:app --reload
```

```bash
# Frontend (separate terminal)
cd app/frontend && npm install && npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies API requests to the backend.

See [app/README.md](app/README.md) for Docker deployment and architecture details.

---

## How It Works

A single prompt like _"Plan a 50 km tour through the Spreewald"_ or _"Plan a 2-week roadtrip through northern Spain"_ generates a complete tour document with route, map, POIs, weather, and transit connections.

Three building blocks make this possible:

### Steering Files

Steering files turn Kiro into a domain-specific tour planner:

| File                       | Scope           | Purpose                                           |
| -------------------------- | --------------- | ------------------------------------------------- |
| `user-preferences.md`      | Always          | Interests, food/accommodation rules, travel group |
| `cycling-tour-planning.md` | `trips/bike/**` | Cycling workflow, BRouter routing, VBB fares      |
| `roadtrip-planning.md`     | `trips/road/**` | Roadtrip workflow, ORS routing, buffer rules      |
| `commit-messages.md`       | Always          | Conventional Commits                              |

### MCP Servers

Eight custom Python servers (FastMCP + httpx), no Node.js:

| Server                                    | Purpose                                          | API                                                                              |
| ----------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------- |
| [`brouter`](mcp/brouter/)                 | Cycling/hiking routing, geocoding, map rendering | [BRouter](https://brouter.de) + [Nominatim](https://nominatim.openstreetmap.org) |
| [`ors`](mcp/ors/)                         | Car/cycling/walking routing, isochrones, matrix  | [OpenRouteService](https://openrouteservice.org/)                                |
| [`osrm`](mcp/osrm/)                       | Car routing with GPX export (road geometry)      | [OSRM](https://project-osrm.org/) (public, no key)                               |
| [`open-meteo`](mcp/open-meteo/)           | Weather forecast + geocoding                     | [Open-Meteo](https://open-meteo.com/)                                            |
| [`vbb`](mcp/vbb/)                         | Stop search, departures, journey planning        | [VBB REST](https://v6.vbb.transport.rest/)                                       |
| [`overpass`](mcp/overpass/)               | POI search along routes                          | [Overpass API](https://overpass-api.de/)                                         |
| [`waymarkedtrails`](mcp/waymarkedtrails/) | Find marked hiking & cycling routes              | [Waymarked Trails](https://waymarkedtrails.org/)                                 |
| [`wikivoyage`](mcp/wikivoyage/)           | Travel guides, destination search, nearby search | [Wikivoyage](https://de.wikivoyage.org/)                                         |

Additionally, `remote_web_search` is used for flights, hotels, car rentals, and events — no stable free API exists for those.

### Hooks

| Hook                  | Trigger                                             | Action                                              |
| --------------------- | --------------------------------------------------- | --------------------------------------------------- |
| GPX Consistency Check | GPX file in `trips/bike/` or `trips/hike/` modified | Re-render map + elevation profile, update distances |

---

## Project Structure

```
app/
├── backend/                 FastAPI + Gemini agent (Python)
└── frontend/                Vue 3 + Leaflet + Tailwind (TypeScript)
lib/
└── src/lib/                 Shared API client library (uv workspace package)
trips/
├── bike/                    Cycling tours: Markdown, GPX, maps
├── hike/                    Hiking tours (planned)
└── road/                    Multi-day car trips
mcp/
├── brouter/                 Cycling/hiking routing + maps
├── ors/                     Car routing (OpenRouteService)
├── osrm/                    Car routing + GPX export (OSRM)
├── open-meteo/              Weather
├── overpass/                POI search (OpenStreetMap)
├── vbb/                     Public transit Berlin/Brandenburg
├── waymarkedtrails/         Marked hiking/cycling routes
└── wikivoyage/              Travel guide content
.kiro/
├── settings/mcp.json        Server configuration
├── hooks/                   Agent hooks
└── steering/                Steering rules
pyproject.toml               uv workspace root + ruff config
.env                         API keys (gitignored)
```

## Tests

```bash
# Run from project root (uv workspace resolves all dependencies)
uv run pytest mcp/brouter/tests/ -v
uv run pytest mcp/open-meteo/tests/ -v
uv run pytest mcp/vbb/tests/ -v
uv run pytest mcp/overpass/tests/ -v
```

## Code Quality

```bash
# Format + lint all Python
uvx ruff format lib/ app/backend/ mcp/
uvx ruff check lib/ app/backend/ mcp/ --fix

# Vulnerability check
uvx pip-audit
cd app/frontend && npm audit
```

## Licenses & Data Sources

| Source                                                   | License      |
| -------------------------------------------------------- | ------------ |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | ODbL         |
| [BRouter](https://brouter.de)                            | MIT          |
| [OpenRouteService](https://openrouteservice.org/)        | MIT          |
| [OSRM](https://project-osrm.org/)                        | BSD-2        |
| [Nominatim](https://nominatim.openstreetmap.org)         | ODbL         |
| [Wikivoyage](https://www.wikivoyage.org/)                | CC BY-SA 3.0 |
| [Waymarked Trails](https://waymarkedtrails.org/)         | ODbL         |
| [Open-Meteo](https://open-meteo.com/)                    | CC BY 4.0    |
| Map Tiles: OpenStreetMap / OpenTopoMap                   | ODbL         |
