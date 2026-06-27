# Trip Planner App

AI-powered tour planner — FastAPI backend with Gemini 2.5 Flash agent + Vue 3 frontend.

## Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+ with npm
- Gemini API key from [Google AI Studio](https://aistudio.google.com)
- ORS API key from [openrouteservice.org](https://openrouteservice.org/dev/#/signup) (for geocoding)

## Setup

```bash
# Environment (project root)
echo "GEMINI_API_KEY=your-key" >> .env
echo "ORS_API_KEY=your-key" >> .env

# Backend
cd app/backend && uv sync

# Frontend
cd app/frontend && npm install
```

## Development

Run in separate terminals:

```bash
# Backend (port 8000)
cd app/backend && uv run uvicorn main:app --reload
```

```bash
# Frontend (port 5173, proxies /api → backend)
cd app/frontend && npm run dev
```

Open http://localhost:5173.

## Production

```bash
# Docker
cd app && docker build -t trip-planner .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key -e ORS_API_KEY=your-key trip-planner

# Without Docker
cd app/frontend && npm run build
cd app/backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Structure

```
app/
├── backend/
│   ├── main.py          # FastAPI app, SSE endpoint, static serving
│   ├── agent.py         # Gemini agent loop (tool calling, retry, streaming)
│   ├── tools.py         # Tool registry (12 tools from lib/)
│   ├── steering.py      # Tour-type detection + system prompt assembly
│   ├── i18n.py          # Bilingual error messages (de/en)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.vue      # Root: SSE parsing, state, split-pane layout
│   │   ├── i18n.ts      # UI translations (de/en)
│   │   └── components/  # ChatInput, TourContent, TourMap
│   ├── vite.config.ts   # Dev proxy to backend
│   └── package.json
└── Dockerfile           # Multi-stage: node build → python serve
```

## API

| Method | Path          | Description                     |
| ------ | ------------- | ------------------------------- |
| POST   | `/api/chat`   | Send prompt, receive SSE stream |
| GET    | `/api/health` | Health check                    |

## Architecture

Gemini 2.5 Flash acts as LLM orchestrator with 12 registered tools (geocoding, routing, weather, transit, route search, travel guides). The agent loop iterates: prompt → tool calls → results → final markdown response, streamed via SSE. Includes retry with exponential backoff for 429/503 errors.

Steering files from `.kiro/steering/` are loaded based on detected tour type:

- **Bike** keywords → `user-preferences.md` + `bike-planning.md` + `bike-template.md`
- **Road** keywords → `user-preferences.md` + `road-planning.md` + `road-template.md`
- **Other** → `user-preferences.md` only

All API logic lives in the shared `lib/` package (uv workspace dependency, used by both the app and MCP servers).

The frontend renders Markdown to HTML using [`marked`](https://github.com/markedjs/marked) + [DOMPurify](https://github.com/cure53/DOMPurify) with Tailwind Typography (`prose` classes). Routes and waypoints are displayed on a Leaflet map in real-time as tool calls complete. UI language (DE/EN) is selectable via toggle.

## Tools

| Tool                   | Source         | API              |
| ---------------------- | -------------- | ---------------- |
| `geocode`              | lib/geocoding  | OpenRouteService |
| `search_location`      | lib/brouter    | Nominatim        |
| `calculate_car_route`  | lib/routing    | OSRM             |
| `calculate_bike_route` | lib/brouter    | BRouter          |
| `weather_forecast`     | lib/weather    | Open-Meteo       |
| `search_routes`        | lib/routes     | Waymarked Trails |
| `search_stops`         | lib/transit    | VBB REST         |
| `get_departures`       | lib/transit    | VBB REST         |
| `get_journeys`         | lib/transit    | VBB REST         |
| `search_destinations`  | lib/wikivoyage | Wikivoyage       |
| `get_article`          | lib/wikivoyage | Wikivoyage       |
| `search_nearby`        | lib/wikivoyage | Wikivoyage       |
