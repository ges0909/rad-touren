# Radtouren-Planer — Web App Concept

AI-powered cycling tour planner for the Berlin/Brandenburg region, turning natural language prompts into complete tour packages with route, map, POIs, weather, and transit connections.

## Vision

A web application where users type a prompt like _"Plan a 50 km tour through the Spreewald with swimming stops"_ and receive a complete, ready-to-ride tour — interactive map, GPX download, points of interest, weather forecast, and verified public transit connections.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                      │
│  HTML + Leaflet + Markdown Rendering            │
│  Prompt input → Streaming response → Map + Tour │
│  Hosted on: Netlify / Railway / Render          │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS (SSE streaming)
┌──────────────────────▼──────────────────────────┐
│                   Backend                       │
│  FastAPI (Python)                               │
│  ┌─────────────────────────────────────────┐    │
│  │  Agent Orchestrator                     │    │
│  │  System Prompt = Steering Document      │    │
│  │  LLM: Google Gemini API (Free Tier)     │    │
│  │  Tool loop: prompt → tool calls →       │    │
│  │             results → next call → done  │    │
│  └──────┬──────┬──────┬──────┬─────────────┘    │
│         │      │      │      │                  │
│  ┌──────▼┐ ┌──▼───┐ ┌▼────┐ ┌▼───────┐          │
│  │BRouter│ │Meteo │ │VBB  │ │Overpass│          │
│  │Routing│ │Wetter│ │ÖPNV │ │POIs    │          │
│  └───────┘ └──────┘ └─────┘ └────────┘          │
│  (existing MCP servers, called as Python libs)  │
│  Hosted on: Railway / Render / Cloud Run        │
└─────────────────────────────────────────────────┘
```

## Components

### Frontend

- **Tech**: Plain HTML + CSS + JavaScript (no framework for MVP)
- **Map**: Leaflet with OpenStreetMap tiles
- **Prompt input**: Text field with example prompts
- **Response display**: Streaming markdown rendering + interactive map with POI markers
- **GPX download**: Direct download button for the generated track
- **Hosting**: Netlify (static) or co-hosted with backend on Railway

### Backend

- **Tech**: FastAPI (Python)
- **LLM**: Google Gemini API via `google-genai` SDK
  - Free Tier: 15 RPM, 1M tokens/day — sufficient for prototype
  - System Instruction: Steering document (radtouren-planung.md)
  - Function Calling: MCP server functions registered as Gemini tools
- **Agent loop**: Iterative tool-calling until the tour is complete
- **Streaming**: Server-Sent Events (SSE) to stream progress to the frontend
- **Hosting**: Railway or Render (Python-native, auto-deploy from GitHub)

### Tool Services (existing MCP servers, reused as Python libraries)

| Service    | Function                          | External API          |
| ---------- | --------------------------------- | --------------------- |
| BRouter    | Route calculation, geocoding, map | brouter.de, Nominatim |
| Open-Meteo | Weather forecast                  | open-meteo.com        |
| VBB        | Public transit connections        | v6.vbb.transport.rest |
| Overpass   | POI search along routes           | overpass-api.de       |

All APIs are free and keyless. The MCP servers are already implemented and tested — they can be imported directly as Python modules instead of running as MCP processes.

## Steering as System Prompt

The existing steering document (`radtouren-planung.md`) becomes the Gemini system instruction. It encodes:

- **Workflow**: Step-by-step tour generation (geocode → route → GPX → map → POIs → weather → transit → markdown)
- **Quality rules**: Coordinate conventions, round-trip enforcement, waypoint placement
- **Output template**: Consistent markdown structure with emoji POI categories
- **Domain knowledge**: Regional cycling routes, transit rules, geographic bounds
- **Safety checks**: SEV disruption detection, weather warnings

The steering document is the core IP — it turns a generic LLM into a domain-specific tour planner.

## User Flow

```
1. User enters: "Plane eine 40 km Tour um den Scharmützelsee mit Badestellen"
2. Frontend sends prompt to backend via POST /api/plan
3. Backend streams progress via SSE:
   → "Suche Orte am Scharmützelsee..."
   → "Berechne Route (42 km, 3 Waypoints)..."
   → "Suche Badestellen und Einkehrmöglichkeiten..."
   → "Prüfe Wetter für Samstag..."
   → "Prüfe Nahverkehr ab Blankenfelde..."
4. Backend returns complete tour:
   → Markdown text (rendered in browser)
   → GPX track (displayed on Leaflet map + download)
   → POI list (markers on map with popups)
   → Weather summary
   → Transit connections with SEV warnings
5. User can download GPX, view interactive map, read tour description
```

## Data Flow

```
User Prompt
    │
    ▼
Gemini API (with steering as system instruction)
    │
    ├─→ search_location("Scharmützelsee")     → coordinates
    ├─→ calculate_route([waypoints])           → GPX + distance
    ├─→ search_pois_along_route(gpx, preset)   → POI list
    ├─→ weather_forecast(lat, lon)             → weather data
    ├─→ search_stops("Bad Saarow")             → stop IDs
    ├─→ get_journeys(blankenfelde, bad_saarow) → connections
    ├─→ web_search("S-Bahn Störungen")         → SEV check
    │
    ▼
Assembled Tour (markdown + GPX + POIs + weather + transit)
    │
    ▼
Frontend (streamed via SSE)
```

## Business Model Options

### Freemium

- **Free**: 2–3 tours/month, basic features
- **Pro** (~5€/month): Unlimited tours, GPX export, saved tours, custom start station
- **Team** (~15€/month): Shared tour library, group planning

### Pay-per-Tour

- ~0.50–1€ per generated tour
- Lower barrier to entry, no subscription commitment

### B2B / Partnerships

- **Tourism boards**: White-label tour planner for regional websites
- **Bike shops / rental**: Embedded tour suggestions for customers
- **Hotels / camping**: "Tours from your doorstep" widget
- **Sponsored POIs**: Restaurants/cafés pay for highlighted placement

### Cost Structure (per tour)

- Gemini API: ~0.01–0.05€ (depending on model and token usage)
- External APIs: 0€ (all free/keyless)
- Hosting: ~0€ (free tiers) to ~5€/month (small instance)
- **Margin is high** — the main cost is LLM tokens

## MVP Scope

### Phase 1: Prototype (static)

- [x] MCP servers for routing, weather, transit, POIs
- [x] Steering document with complete workflow
- [x] Static tour pages on GitHub Pages
- [x] Interactive Leaflet map with POI markers
- [ ] Finish and test interactive map (experimental/map.html)

### Phase 2: Web App MVP

- [ ] FastAPI backend with Gemini integration
- [ ] Register MCP server functions as Gemini tools
- [ ] Agent loop with streaming (SSE)
- [ ] Minimal frontend: prompt input + map + markdown display
- [ ] Deploy on Railway
- [ ] Basic rate limiting (IP-based)

### Phase 3: Product

- [ ] User management: registration, login (OAuth via Google/GitHub + email/password)
- [ ] User profiles: custom home station, preferred tour length, interests (art, swimming, nature, etc.)
- [ ] Saved tours library (per user)
- [ ] Tour sharing (public URLs)
- [ ] Payment integration (Stripe) for Pro subscriptions or pay-per-tour
- [ ] Usage tracking and billing dashboard
- [ ] Mobile-friendly responsive design
- [ ] Multi-region support (configurable steering per region)

### Phase 4: Growth

- [ ] Social features: tour ratings, comments, community favorites
- [ ] Tour templates: curated starting points users can customize
- [ ] Seasonal recommendations (automatic, based on weather + events)
- [ ] API access for B2B partners (tourism boards, bike shops)
- [ ] White-label option for regional tourism websites
- [ ] Native mobile app (or PWA)

## Technical Decisions

| Decision               | Choice                        | Rationale                                               |
| ---------------------- | ----------------------------- | ------------------------------------------------------- |
| LLM                    | Google Gemini                 | Free tier, good function calling, fast                  |
| Backend framework      | FastAPI                       | Python (matches MCP servers), async, streaming support  |
| Frontend               | Plain HTML + Leaflet          | No build step, fast iteration, upgrade later            |
| Map library            | Leaflet → MapLibre            | Leaflet for MVP, MapLibre GL for product (vector tiles) |
| Hosting                | Railway                       | Simple deploy, Python-native, free tier                 |
| MCP server integration | Direct Python import          | No MCP protocol overhead, just call functions directly  |
| Streaming              | SSE                           | Simple, works everywhere, no WebSocket complexity       |
| Authentication         | OAuth (Google/GitHub) + email | Low friction signup, widely supported                   |
| Payment                | Stripe                        | Industry standard, good API, supports subscriptions     |
| Database               | PostgreSQL (Railway)          | User data, saved tours, usage tracking                  |

## Deployment Options

### Frontend Hosting

| Platform     | Free Tier                | Pros                                | Cons                                |
| ------------ | ------------------------ | ----------------------------------- | ----------------------------------- |
| GitHub Pages | Unlimited (public repos) | Already in use, zero config         | Static only, no API routes          |
| Vercel       | 100 GB bandwidth/month   | Fast, edge network, preview deploys | Serverless functions are Node-first |
| Netlify      | 100 GB bandwidth/month   | Easy deploy, custom domains, CDN    | No Python backend                   |

For the prototype, frontend is co-hosted with the backend (see below). Dedicated frontend hosting only becomes relevant when separating concerns for production (CDN, edge caching).

### Backend Hosting (serves both API and frontend for MVP)

| Platform         | Free Tier                 | Pros                                                               | Cons                            |
| ---------------- | ------------------------- | ------------------------------------------------------------------ | ------------------------------- |
| Railway          | 500 hrs/month, 512 MB RAM | Simple, GitHub auto-deploy, Python-native, serves static files too | Free tier may not cover 24/7    |
| Render           | 750 hrs/month, 512 MB RAM | Similar to Railway, good docs                                      | Cold starts on free tier (~30s) |
| Google Cloud Run | 2M requests/month free    | Pay-per-request, scales to zero                                    | More setup, GCP account needed  |
| Fly.io           | 3 shared VMs, 256 MB RAM  | Global edge network, low latency                                   | Requires credit card, Docker    |
| Koyeb            | 1 service, no cold starts | Always-on free tier                                                | Limited resources               |

### Recommended Setup

**Prototype**: Railway — single service serving FastAPI backend + static frontend. One repo, one deploy, no CORS.

**Production**: Railway or Render (backend API) + Vercel or Netlify (frontend CDN) — separates concerns, scales independently, edge-cached frontend.

## Scaling

### Bottlenecks

A single tour generation involves ~6–10 sequential LLM calls and ~10 external API requests. Total time: 30–60 seconds per tour. This limits throughput per server instance.

| Component        | Constraint                          | Mitigation                                          |
| ---------------- | ----------------------------------- | --------------------------------------------------- |
| LLM API          | Gemini Free: 15 RPM, 1M tokens/day  | Upgrade to paid tier (~$0.01/tour), or queue system |
| BRouter          | Public API, no SLA                  | Self-host BRouter instance for reliability          |
| Overpass API     | Rate-limited, shared infrastructure | Cache POI results per route (POIs rarely change)    |
| VBB API          | Public, occasionally slow           | Cache connections per station pair + date           |
| Concurrent users | Each tour blocks a thread for ~60s  | Async workers, task queue (Celery/ARQ)              |

### Scaling Strategy

**Phase 2 (MVP, 1–50 users):**

- Single Railway instance, async FastAPI
- No caching, no queue — sequential processing is fine
- Gemini Free Tier sufficient

**Phase 3 (Product, 50–500 users):**

- Gemini paid tier (pay-per-token)
- Redis cache for POIs, weather, transit connections
- Background task queue (ARQ or Celery) — user submits prompt, gets notified when tour is ready
- PostgreSQL for user data and saved tours

**Phase 4 (Growth, 500+ users):**

- Multiple backend instances behind load balancer (Railway or Cloud Run auto-scaling)
- Self-hosted BRouter for routing independence
- CDN for frontend (Vercel/Netlify)
- Pre-generated tour suggestions (popular routes cached, personalized on demand)
- Regional expansion: separate steering documents + transit APIs per region, same infrastructure

### Kubernetes

Not recommended until Phase 4+. Railway and Cloud Run provide container-based auto-scaling without the operational overhead of managing a K8s cluster. Kubernetes becomes relevant when:

- Multiple independently scaling services (separate worker pools, self-hosted BRouter, dedicated LLM proxy)
- Complex deployment patterns (canary releases, blue-green deployments)
- Multi-region with service mesh
- Team size requires GitOps workflows

Managed K8s options (GKE, EKS, DigitalOcean Kubernetes) reduce ops burden but still add ~20–40€/month base cost before any workload. For this project, Cloud Run or Railway cover the same scaling needs at lower complexity and cost.

### Cost Projection

| Users/month | Tours/month | LLM cost    | Hosting | Total       |
| ----------- | ----------- | ----------- | ------- | ----------- |
| 10          | 30          | ~$0         | ~$0     | ~$0         |
| 100         | 300         | ~$3–15      | ~$7     | ~$10–22     |
| 1,000       | 3,000       | ~$30–150    | ~$25    | ~$55–175    |
| 10,000      | 30,000      | ~$300–1,500 | ~$100   | ~$400–1,600 |

At 5€/month subscription with 10% conversion: 1,000 free users → 100 paying → 500€/month revenue. Breaks even at ~200–300 active users.

## Risks

- **LLM quality**: Gemini may not follow the steering as precisely as Claude in Kiro. Needs testing and prompt tuning.
- **Rate limits**: Free tier limits may be hit with multiple users. Mitigation: caching, queue system.
- **External API reliability**: BRouter/Overpass/VBB can have outages. Mitigation: graceful degradation (already in steering).
- **Fahrradmitnahme accuracy**: SEV bus restrictions are not always in structured data. Mitigation: web scraping + explicit warnings.
- **Regional lock-in**: Currently Berlin/Brandenburg only. Expansion requires new steering documents and transit APIs per region.
