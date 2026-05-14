# Trip Planner — Web App Concept

AI-powered tour planner for cycling (Berlin/Brandenburg), hiking, and road trips across Europe. Natural language prompts produce complete tour packages with routes, maps, POIs, weather, ratings, and travel connections.

## Vision

A single-page web app where users type prompts like _"Plan a 50 km cycling tour through the Spreewald with swimming stops"_ or _"Plan a 2-week road trip along the Spanish north coast"_ and receive a complete tour — interactive map, GPX download, rated POIs, weather, accommodations, and travel connections.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Vite + TypeScript)           │
│  Chat input → SSE stream → Map + Tour + Downloads│
└──────────────────────┬──────────────────────────┘
                       │ SSE (same origin, no CORS)
┌──────────────────────▼──────────────────────────┐
│  Backend (FastAPI, Python)                       │
│  ┌────────────────────────────────────────┐     │
│  │ Agent: Gemini + Steering + Tool Loop   │     │
│  └────┬──────┬──────┬──────┬──────┬───────┘     │
│       │      │      │      │      │             │
│  BRouter  OSRM   ORS  Meteo  VBB  Overpass     │
│  Wikivoyage  Waymarked Trails                   │
│  (MCP servers as Python imports)                │
│                                                 │
│  Hosted on: Railway ($5/Mo, single container)   │
└─────────────────────────────────────────────────┘
```

Single deploy: FastAPI serves the Vue build as static files + API endpoints. No separate frontend hosting.

## LLM Role: Orchestrator & Author

The LLM is both **planner** and **author** — no separate generation engine.

1. **Plans**: Reads steering, interprets prompt, decides workflow
2. **Calls tools**: Geocoding, routing, weather, POIs, ratings
3. **Synthesizes**: Combines API data into coherent tour
4. **Generates**: Writes descriptions, tips, summaries following the template

**From APIs (facts):** coordinates, distances, weather, POI names, ratings, transit.
**From LLM (creative):** day plans, POI descriptions, tips, packing lists, chat responses.

### Agent Loop

```
User Prompt → LLM (with steering)
  ├─→ geocode("Bilbao") → [lon, lat]
  ├─→ driving_time(A, B) → 198 km, 2.5h
  ├─→ search_routes("Picos") → route list
  ├─→ weather_forecast(lat, lon) → JSON
  ├─→ ... (6–10 iterations)
  └─→ Final markdown response (streamed to frontend)
```

## Steering: Dual Use

The `.kiro/steering/` files serve two consumers from one source:

- **Kiro (development)**: Loaded automatically for interactive planning.
- **Web App (production)**: Backend reads them at startup as LLM system prompt.

```python
def build_system_prompt(tour_type: str) -> str:
    files = ["user-preferences.md"]
    if tour_type == "road":
        files += ["road-planning.md", "road-template.md"]
    elif tour_type == "bike":
        files += ["bike-planning.md", "bike-template.md"]
    return "\n\n".join(Path(f".kiro/steering/{f}").read_text() for f in files)
```

Workflow: Develop steering in Kiro → push → auto-deploy → web app uses updated steering.

## Tour Types

| Type       | Scope                        | Key Tools                        | Output                               |
| ---------- | ---------------------------- | -------------------------------- | ------------------------------------ |
| Cycling    | Berlin/Brandenburg day trips | BRouter, VBB, Overpass, Meteo    | GPX + map + POIs + transit + weather |
| Road trips | Europe, multi-day            | OSRM, ORS, Wikivoyage, Waymarked | Route + map + hotels + POIs + costs  |
| Hiking     | Anywhere (planned)           | Waymarked Trails, ORS, Meteo     | Route + ratings + weather            |

## Frontend

- **Framework**: Vue 3 + Vite + TypeScript + Tailwind CSS
- **Tooling**: ESLint + Prettier, strict TypeScript, npm
- **Layout**: Single page — chat input at top, tour result below
- **Responsive Web Design**: CSS media queries for mobile (stacked), tablet (chat + map side-by-side), desktop (three columns possible)
- **Map** (vue-leaflet → MapLibre GL for production):
  - Colored route line (clickable for segment info)
  - POI markers with category icons + popups
  - Station markers (click → jump to tour section)
  - Hover tooltips for distances
  - Zoom-to-fit / zoom-to-station
- **Landing/Intro**: Brief explanation above the chat — what the app does, example prompts, supported tour types
- **Downloads**: Markdown, PDF (html2pdf.js or WeasyPrint), GPX
- **Language**: Detects user input language, responds in same language

## Backend

- **Framework**: FastAPI (Python 3.12+, async)
- **Tooling**:  for dependency management,  (no requirements.txt, no pip)
- **LLM**: Google Gemini 2.0 Flash (free tier: 15 RPM, 1M tokens/day)
- **Streaming**: Server-Sent Events (SSE)
- **Hosting**: Railway ($5/Mo) — serves frontend + API in one container

## Tool Services

| Service          | External API            | Tour Types    |
| ---------------- | ----------------------- | ------------- |
| BRouter          | brouter.de, Nominatim   | Cycling       |
| OSRM             | router.project-osrm.org | Road trips    |
| ORS              | openrouteservice.org    | Road trips    |
| Open-Meteo       | open-meteo.com          | All           |
| VBB              | v6.vbb.transport.rest   | Cycling       |
| Overpass         | overpass-api.de         | Cycling, Road |
| Wikivoyage       | wikivoyage.org          | Road trips    |
| Waymarked Trails | waymarkedtrails.org     | Hiking, Road  |

All APIs free and keyless. MCP servers already implemented in `mcp/`.

### Integration Strategy

| Phase      | Approach             | Detail                                                            |
| ---------- | -------------------- | ----------------------------------------------------------------- |
| MVP        | Direct Python import | Import functions from `mcp/*/server.py`, register as Gemini tools |
| Production | MCP Client           | Subprocesses in same container, MCP protocol (identical to Kiro)  |

## API Design

### Endpoints

| Method | Path                    | Purpose                         |
| ------ | ----------------------- | ------------------------------- |
| POST   | `/api/chat`             | Send prompt, receive SSE stream |
| GET    | `/api/tour/:id`         | Retrieve saved tour             |
| GET    | `/api/download/:id.gpx` | GPX download                    |
| GET    | `/api/download/:id.pdf` | PDF download                    |
| GET    | `/api/download/:id.md`  | Markdown download               |

### SSE Events

| Event    | Payload               | Purpose                    |
| -------- | --------------------- | -------------------------- |
| `status` | `{"message": "..."}`  | Progress (shown in chat)   |
| `tour`   | `{"markdown": "..."}` | Tour content (incremental) |
| `map`    | `{"geojson": {...}}`  | Map data for Leaflet       |
| `done`   | `{"tour_id": "..."}`  | Enables downloads          |
| `error`  | `{"message": "..."}`  | Error handling             |

### State

- MVP: In-memory chat history, filesystem for tours (markdown + GPX)
- Production: PostgreSQL (users, sessions, saved tours)

## Gemini Tool Registration

```python
from google.genai import types

geocode_tool = types.FunctionDeclaration(
    name="geocode",
    description="Geocode a place name to coordinates",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "query": types.Schema(type="STRING"),
            "country": types.Schema(type="STRING"),
        },
        required=["query"],
    ),
)

TOOL_REGISTRY = {
    "geocode": ors_geocode,
    "driving_time": ors_driving_time,
    "calculate_route": brouter_calculate_route,
    "weather_forecast": meteo_weather_forecast,
    "search_routes": waymarked_search_routes,
}
```

## Quality Assurance

| Category      | Source                     | Threshold  | Min. Reviews |
| ------------- | -------------------------- | ---------- | ------------ |
| Hiking routes | AllTrails, Komoot, Wikiloc | ≥4.0 stars | ≥30          |
| Hotels        | booking.com                | ≥8.5/10    | ≥50          |
| Restaurants   | TripAdvisor                | ≥4.0/5     | ≥50          |

Cross-check via secondary sources when data is sparse.

## Project Structure

```
app/
├── backend/
│   ├── main.py          # FastAPI, SSE streaming
│   ├── agent.py         # Gemini agent loop
│   ├── tools.py         # Tool declarations + registry
│   └── steering.py      # Load steering files
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/  # ChatInput, TourMap, TourContent
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
└── Dockerfile           # Build frontend, serve via FastAPI

### Local Development

- Terminal 1: `cd app/backend && uvicorn main:app --reload`
- Terminal 2: `cd app/frontend && npm run dev`
- Vite proxies `/api/*` to backend (vite.config.ts)
.kiro/steering/          # Shared: Kiro + web app
mcp/                     # MCP server implementations
trips/                   # Generated tour documents
scripts/                 # Map rendering utilities
```

## Implementation Plan

### Spike (validate core)

1. Single endpoint `POST /api/chat`
2. Load one steering file as system prompt
3. Register 2–3 tools (geocode, driving_time, weather)
4. Test Gemini tool-calling loop with `curl`
5. Success: Gemini calls tools correctly, produces coherent response

### Phase 1: Prototype (static) ✅

- [x] MCP servers for routing, weather, transit, POIs
- [x] Steering documents with complete workflows
- [x] Static tour pages on GitHub Pages
- [x] Cycling + road trip tours with ratings

### Phase 2: Web App MVP

- [ ] FastAPI + Gemini agent loop with SSE
- [ ] Vue 3 frontend (chat + map + tour display)
- [ ] Deploy on Railway (single container)
- [ ] Basic rate limiting

### Phase 3: Product

- [ ] User management (OAuth)
- [ ] Saved tours, sharing (public URLs)
- [ ] Payment (Stripe)
- [ ] Multi-region support

### Phase 4: Growth

- [ ] Social features (ratings, comments)
- [ ] B2B API, white-label
- [ ] PWA / native app

## Business Model

### Revenue Options

- **Freemium**: 2–3 tours/month free, Pro ~5€/month (unlimited)
- **Pay-per-tour**: ~0.50–1€ per tour
- **B2B**: White-label for tourism boards, bike shops, hotels

### Cost per Tour

- LLM: ~0.01–0.05€
- APIs: 0€ (all free)
- Hosting: ~$5/month base
- **High margin** — main cost is LLM tokens

### Projection

| Users/month | Tours | LLM  | Hosting | Total |
| ----------- | ----- | ---- | ------- | ----- |
| 10          | 30    | ~$0  | ~$5     | ~$5   |
| 100         | 300   | ~$10 | ~$7     | ~$17  |
| 1,000       | 3,000 | ~$90 | ~$25    | ~$115 |

Break-even at ~200 paying users (5€/month, 10% conversion).

## Risks

- **LLM quality**: Gemini may follow steering less precisely than Claude. Needs prompt tuning.
- **Rate limits**: Free tier (15 RPM) limits concurrent users. Mitigation: queue, caching.
- **API reliability**: External APIs can have outages. Mitigation: graceful degradation.
- **Regional lock-in**: Expansion requires new steering + transit APIs per region.
