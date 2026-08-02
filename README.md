# 🗺️ Gerrit on Tour — AI-Powered Travel Planning

AI-powered tour planning with 13 custom MCP servers for routing, weather, POIs, public transit, and travel content. Plan complete bike tours and multi-day roadtrips through natural language prompts.

| Tour Type    | Description                                         | Status |
| ------------ | --------------------------------------------------- | ------ |
| 🚴 Biking    | Day trips in Berlin/Brandenburg via regional trains | Active |
| 🚗 Roadtrips | Multi-day car rental trips across Europe            | Active |

**→ [Biking Tours](trips/bike/README.md)** · **→ [Roadtrips](trips/road/README.md)**

---

## What It Does

Type a prompt like:

- _"Plan a 60 km bike tour through the Spreewald with swimming stops"_
- _"Plan a 10-day road trip along the northern Spanish coast"_

Get a complete tour plan:
- ✅ Route with GPX track and rendered map
- ✅ Accommodation recommendations (ratings, prices, booking links)
- ✅ Hiking trails with ratings from AllTrails/Komoot
- ✅ Swimming spots, restaurants, museums, art galleries
- ✅ Weather forecast for travel dates
- ✅ Public transit connections (bike tours) or driving times (roadtrips)
- ✅ Markdown document ready to commit

All saved in `trips/bike/` or `trips/road/` with GPX files and map images.

---

## How It Works

**Two ways to use:**

### 1. In Kiro (Primary Workflow)

Open this project in [Kiro](https://kiro.dev) and type your tour request:

1. **MCP servers** provide data via tool calling (routing, weather, POIs, transit)
2. **Steering files** guide the planning workflow (preferences, output format, rules)
3. **Kiro's LLM** orchestrates everything and writes the tour document
4. Results are saved as Markdown + GPX in `trips/{bike|road}/{tour-name}/`

The LLM is both **planner** and **author** — it doesn't just route, it researches, prioritizes, and writes cohesive tour descriptions.

### 2. Web App (Standalone)

A browser UI that replicates the Kiro workflow without requiring the IDE:

- **Frontend:** Vue 3 + Vite + TypeScript + Leaflet
- **Backend:** FastAPI + Google Gemini 2.5 Flash (SSE streaming)
- **MCP Manager:** Subprocess manager spawning MCP servers on demand

```bash
# Run locally
cd app/backend && uv run uvicorn main:app --reload  # Port 8000
cd app/frontend && npm install && npm run dev        # Port 5173 (proxies /api)
```

Open http://localhost:5173 and start planning.

## Quickstart

### Prerequisites

- **Python:** 3.12+ (managed by [uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js:** 20+ (for frontend)
- **API Keys:** Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your-key        # Free: https://aistudio.google.com
ORS_API_KEY=your-key           # Free: https://openrouteservice.org/dev/#/signup
TAVILY_API_KEY=your-key        # Free (1000 req/month): https://tavily.com
SERPAPI_API_KEY=your-key       # Optional: https://serpapi.com (flight search)
```

All other MCP servers use free/public APIs without keys.

### Use with Kiro

1. Install [Kiro](https://kiro.dev)
2. Open this project folder
3. Type your tour request in chat (e.g., _"Plan a bike tour from Berlin to Potsdam"_)
4. Results are saved in `trips/bike/` or `trips/road/`

MCP servers are auto-configured via `.kiro/settings/mcp.json`.

### Run the Web App (Optional)

```bash
# Backend
cd app/backend && uv run uvicorn main:app --reload

# Frontend (separate terminal)
cd app/frontend && npm install && npm run dev
```

Open http://localhost:5173

### Docker (Production)

```bash
cd app && docker build -t gerrit-on-tour .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=... \
  -e ORS_API_KEY=... \
  -e TAVILY_API_KEY=... \
  gerrit-on-tour
```

---

---

## MCP Servers (13 Custom Tools)

Self-contained Python servers providing tour planning capabilities via [Model Context Protocol](https://modelcontextprotocol.io/):

| Server                                    | Purpose                                  | API / Data Source                    | Key Required |
| ----------------------------------------- | ---------------------------------------- | ------------------------------------ | ------------ |
| [`brouter`](mcp/brouter/)                 | Bike routing, map rendering, elevation   | BRouter + Nominatim                  | No           |
| [`ors`](mcp/ors/)                         | Car/foot routing, isochrones, matrix     | OpenRouteService                     | Yes          |
| [`osrm`](mcp/osrm/)                       | Car routing + GPX export                 | OSRM (public)                        | No           |
| [`open-meteo`](mcp/open-meteo/)           | Weather forecast + geocoding             | Open-Meteo                           | No           |
| [`vbb`](mcp/vbb/)                         | Public transit (Berlin/Brandenburg)      | VBB REST API                         | No           |
| [`overpass`](mcp/overpass/)               | POI search along GPX routes              | OpenStreetMap Overpass API           | No           |
| [`waymarkedtrails`](mcp/waymarkedtrails/) | Marked cycling routes                    | Waymarked Trails                     | No           |
| [`wikivoyage`](mcp/wikivoyage/)           | Travel guides, destination search        | Wikivoyage                           | No           |
| [`tavily`](mcp/tavily/)                   | Web search (hotels, restaurants, etc.)   | Tavily Search API                    | Yes          |
| [`serpapi-flights`](mcp/serpapi-flights/) | Flight search via Google Flights         | SerpAPI                              | Yes          |
| [`travel-content`](mcp/travel-content/)   | Travel article search + route tips       | Tavily (quality press)               | Yes          |
| [`travel-videos`](mcp/travel-videos/)     | Public broadcaster videos + transcripts  | YouTube (ÖR channels)                | No           |
| [`podcasts`](mcp/podcasts/)               | Travel podcast search + transcripts      | iTunes Search API                    | No           |

**Architecture:** FastMCP + httpx, spawned as subprocesses via stdio JSON-RPC. Each server is self-contained with its own `pyproject.toml`.

## Steering Files (Planning Rules)

Steering files in `.kiro/steering/` define preferences, workflow, and output format. Loaded automatically via `fileMatch` patterns:

**Universal (always loaded):**
- `user-preferences.md` — Home base, interests, content integrity rules

**Bike tours (`trips/bike/**`):**
- `bike-preferences.md` — Distance limits, terrain, interests priority, food/drink rules
- `bike-planner.md` — Workflow (BRouter routing, VBB transit, Overpass POIs)
- `bike-output-template.md` — Markdown structure and formatting

**Roadtrips (`trips/road/**`):**
- `road-preferences.md` — Flight preferences, accommodation rules, hiking priorities
- `road-planner.md` — Workflow (ORS/OSRM routing, flight search, daily driving limits)
- `road-output-template.md` — Markdown structure and formatting

The `fileMatch` system ensures only relevant rules are loaded per tour type, preventing context bloat.

---

---

## Project Structure

```
├── app/
│   ├── backend/              FastAPI + Gemini agent
│   │   ├── main.py           SSE endpoint, MCP lifecycle
│   │   ├── agent.py          Gemini tool calling loop
│   │   ├── mcp_manager.py    MCP subprocess manager
│   │   └── steering.py       Load steering files
│   └── frontend/             Vue 3 + Leaflet + Tailwind
├── mcp/                      13 MCP servers (self-contained)
│   ├── brouter/              Bike routing + maps
│   ├── ors/                  Car routing (OpenRouteService)
│   ├── osrm/                 Car routing + GPX export
│   ├── open-meteo/           Weather forecasts
│   ├── vbb/                  Berlin/Brandenburg transit
│   ├── overpass/             POI search (OpenStreetMap)
│   ├── waymarkedtrails/      Marked cycling routes
│   ├── wikivoyage/           Travel guide content
│   ├── tavily/               Web search
│   ├── serpapi-flights/      Flight search (Google Flights)
│   ├── travel-content/       Travel articles + route tips
│   ├── travel-videos/        Public broadcaster videos
│   └── podcasts/             Podcast search + transcripts
├── trips/
│   ├── bike/{tour-name}/     Bike tour documents
│   │   ├── index.md          Tour description (German)
│   │   ├── gpx/              GPX tracks
│   │   └── img/              Route maps, elevation profiles
│   └── road/{trip-name}/     Roadtrip documents
│       ├── index.md          Trip description (German)
│       ├── gpx/              Car route GPX per day
│       └── img/              Route maps per driving day
├── .kiro/
│   ├── settings/mcp.json     MCP server configuration
│   └── steering/             Planning rules (fileMatch-based)
├── scripts/                  Map rendering utilities
├── ruff.toml                 Linter/formatter config
└── .env                      API keys (gitignored)
```

---

## Development

### Testing

```bash
cd app/backend && uv run pytest tests/ -v
```

### Code Quality

```bash
uvx ruff check .    # Lint
uvx ruff format .   # Format
```

Ruff config: `ruff.toml` (Python 3.12, line-length 100, double quotes)

### MCP Server Development

Each server is self-contained in `mcp/{name}/`:

```
mcp/{name}/
├── server.py          # FastMCP app, tool declarations
├── {name}.py          # Pure HTTP client (no FastMCP dependency)
├── pyproject.toml     # Dependencies (uv-managed)
└── tests/             # pytest + pytest-asyncio
```

Run a server standalone:
```bash
cd mcp/brouter && uv run python server.py
```

See [`docs/mcp-development.md`](docs/mcp-development.md) for detailed guidelines.

---

## Advanced Features

### Cross-LLM Trip Review

Before traveling, review finished trip plans with an independent LLM to catch errors the planning agent might miss.

Save reviews as `review.md` in the trip folder (e.g., `trips/road/nordspanien-kueste/review.md`).

**Example review prompt:**

```
Review this roadtrip plan for correctness and plausibility:

1. Verify dates and weekdays match (use a calendar for {year})
2. Check driving distances — are they realistic?
3. Are museums/attractions scheduled on their closing days?
4. Are flight times plausible for the stated airline/route?
5. Flag any events that might not occur on stated dates
6. Suggest timing optimizations (e.g., reorder stops to avoid closures)
7. Note missing practical info (advance bookings, seasonal closures)

Output: confirmed OK, issues found, suggested optimizations.
```

### Context Management

The project uses a **two-layer context system**:

1. **AGENTS.md** (repo root) — Universal rules for all AI assistants (Conventional Commits, project overview)
2. **`.kiro/steering/*.md`** — Context-specific rules loaded via fileMatch patterns

See [`docs/Context-Management.md`](docs/Context-Management.md) for details.

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
