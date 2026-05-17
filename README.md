# 🗺️ Gerrit on Tour — Cycling, Hiking & Roadtrips

AI-powered tour planning with custom MCP servers for routing, weather, POIs, public transit, and travel guide content.

| Category     | Description                                         | Status  |
| ------------ | --------------------------------------------------- | ------- |
| 🚴 Cycling   | Day trips in Berlin/Brandenburg via regional trains | Active  |
| 🥾 Hiking    | Day hikes in Berlin/Brandenburg                     | Planned |
| 🚗 Roadtrips | Multi-day car rental trips across Europe            | Active  |

**→ [Cycling Tours](trips/bike/README.md)** · **→ [Hiking Tours](trips/hike/README.md)** · **→ [Roadtrips](trips/road/README.md)**

---

## Vision

Two ways to plan tours:

1. **In Kiro** (primary) — open this project in [Kiro](https://kiro.dev), type a prompt, and the MCP servers + steering files turn Kiro into a specialized tour planner. Results land as Markdown + GPX in `trips/`.
2. **Web App** (spin-off) — a standalone chat UI that uses the same MCP servers and steering files, accessible without Kiro via browser.

A single prompt like _"Plan a 50 km cycling tour through the Spreewald with swimming stops"_ or _"Plan a 2-week road trip along the Sardinian coast"_ produces complete tours — route, map, POIs, weather, accommodations, and travel connections.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Vite + TypeScript + Leaflet) │
│  Chat input → SSE stream → Map + Markdown       │
└──────────────────────┬──────────────────────────┘
                       │ POST /api/chat (SSE)
┌──────────────────────▼──────────────────────────┐
│  Backend (FastAPI + Gemini 2.5 Flash)           │
│  ┌────────────────────────────────────────┐     │
│  │ Agent Loop: Steering + Tool Calling    │     │
│  └────┬──────────────────────────────┬────┘     │
│       │ stdio JSON-RPC               │          │
│  ┌────▼────────────────────────┐     │          │
│  │ MCP Manager (subprocess)    │     │          │
│  │ 9 servers, lazy spawn       │     │          │
│  └─────────────────────────────┘     │          │
└──────────────────────────────────────────────────┘
```

The LLM is both **planner** and **author**: it reads steering files, calls tools for facts (coordinates, distances, weather), and synthesizes everything into a coherent tour document.

---

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/getting-started/installation/) + Node.js 20+

```bash
# API keys (.env in project root, gitignored)
echo "GEMINI_API_KEY=your-key" >> .env
echo "ORS_API_KEY=your-key" >> .env
echo "TAVILY_API_KEY=your-key" >> .env
```

- Gemini API key (free): [Google AI Studio](https://aistudio.google.com)
- OpenRouteService key (free): [openrouteservice.org](https://openrouteservice.org/dev/#/signup)
- Tavily key (free, 1000 req/month): [tavily.com](https://tavily.com)

All other MCP servers use free APIs without a key.

### Use with Kiro

Open this project in [Kiro](https://kiro.dev). The MCP servers in `mcp/` are auto-configured via `.kiro/settings/mcp.json`. Steering files in `.kiro/steering/` guide the planning workflow. Just type your tour request in the chat.

### Run the Web App

```bash
# Backend (port 8000)
cd app/backend && uv run uvicorn main:app --reload

# Frontend (port 5173, separate terminal)
cd app/frontend && npm install && npm run dev
```

Open http://localhost:5173 — Vite proxies `/api` to the backend.

```bash
# Docker (production)
cd app && docker build -t gerrit-on-tour .
docker run -p 8000:8000 -e GEMINI_API_KEY=... -e ORS_API_KEY=... -e TAVILY_API_KEY=... gerrit-on-tour
```

---

## MCP Servers

Nine Python servers (FastMCP + httpx), spawned as subprocesses via stdio JSON-RPC:

| Server                                    | Purpose                                          | API                                                                              |
| ----------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------- |
| [`brouter`](mcp/brouter/)                 | Cycling/hiking routing, geocoding, map rendering | [BRouter](https://brouter.de) + [Nominatim](https://nominatim.openstreetmap.org) |
| [`ors`](mcp/ors/)                         | Car/cycling/walking routing, isochrones, matrix  | [OpenRouteService](https://openrouteservice.org/)                                |
| [`osrm`](mcp/osrm/)                       | Car routing with road geometry + GPX export      | [OSRM](https://project-osrm.org/) (public, no key)                               |
| [`open-meteo`](mcp/open-meteo/)           | Weather forecast + geocoding                     | [Open-Meteo](https://open-meteo.com/)                                            |
| [`vbb`](mcp/vbb/)                         | Stop search, departures, journey planning        | [VBB REST](https://v6.vbb.transport.rest/)                                       |
| [`overpass`](mcp/overpass/)               | POI search along routes                          | [Overpass API](https://overpass-api.de/)                                         |
| [`waymarkedtrails`](mcp/waymarkedtrails/) | Find marked hiking & cycling routes              | [Waymarked Trails](https://waymarkedtrails.org/)                                 |
| [`wikivoyage`](mcp/wikivoyage/)           | Travel guides, destination search, nearby search | [Wikivoyage](https://de.wikivoyage.org/)                                         |
| [`tavily`](mcp/tavily/)                   | Web search for hotels, flights, current info     | [Tavily](https://tavily.com/)                                                    |

## Steering Files

Steering files in `.kiro/steering/` serve as system prompt for the Gemini agent:

| File                  | Scope         | Purpose                                           |
| --------------------- | ------------- | ------------------------------------------------- |
| `user-preferences.md` | Always        | Interests, food/accommodation rules, travel group |
| `bike-planning.md`    | Cycling tours | Workflow, BRouter routing, VBB fares              |
| `road-planning.md`    | Roadtrips     | Workflow, ORS/OSRM routing, buffer rules          |
| `bike-template.md`    | Cycling tours | Output template structure                         |
| `road-template.md`    | Roadtrips     | Output template structure                         |

---

## Project Structure

```
app/
├── backend/                 FastAPI + Gemini agent (Python)
│   ├── main.py              App entry, SSE endpoint, MCP lifecycle
│   ├── agent.py             Gemini agent loop with tool calling
│   ├── mcp_manager.py       MCP subprocess manager (lazy spawn, JSON-RPC)
│   └── steering.py          Load steering files → system prompt
└── frontend/                Vue 3 + Leaflet + Tailwind (TypeScript)
mcp/
├── brouter/                 Cycling/hiking routing + maps
├── ors/                     Car routing (OpenRouteService)
├── osrm/                    Car routing + GPX export (OSRM)
├── open-meteo/              Weather
├── overpass/                POI search (OpenStreetMap)
├── vbb/                     Public transit Berlin/Brandenburg
├── waymarkedtrails/         Marked hiking/cycling routes
├── wikivoyage/              Travel guide content
└── tavily/                  Web search (Tavily)
trips/
├── bike/                    Cycling tours (per-trip folders)
│   ├── README.md
│   └── {tour-name}/
│       ├── index.md         Tour description
│       ├── gpx/             GPX tracks
│       └── img/             Route maps, elevation profiles
├── hike/                    Hiking tours (planned)
└── road/                    Multi-day car trips (per-trip folders)
    ├── README.md
    └── {trip-name}/
        ├── index.md         Trip description
        ├── gpx/             Car route GPX per driving day
        └── img/             Route maps per driving day
scripts/                     Map rendering utilities (see scripts/README.md)
.kiro/steering/              Steering rules for the agent
ruff.toml                    Linter/formatter config
.env                         API keys (gitignored)
```

## Tests

```bash
cd app/backend && uv run pytest tests/ -v
```

## Code Quality

```bash
uvx ruff check .
uvx ruff format .
```

## Trip Review (Cross-LLM Verification)

Before traveling, run the finished trip plan through an independent LLM for a second opinion. This catches factual errors, outdated info, and logical gaps that the planning agent might miss.

Save the review as `review.md` in the trip folder (e.g., `trips/road/nordspanien-kueste/review.md`).

**Example prompt (paste the full trip markdown as context):**

```
Review this roadtrip plan for correctness and plausibility:

1. Verify all dates and weekdays match (use a calendar for {year}).
2. Check driving distances between cities — are they realistic?
3. Are any museums/attractions scheduled on their closing day?
4. Are flight days and times plausible for the stated airline/route?
5. Flag any events mentioned that might not occur on the stated dates.
6. Suggest timing optimizations (e.g., reorder stops to avoid closures).
7. Note any missing practical info (advance bookings, seasonal closures).

Output a structured review with: confirmed OK, issues found, and suggested optimizations.
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
