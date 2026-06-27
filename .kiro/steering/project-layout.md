# Project Structure

```
rad-touren/
├── .env                        API keys (gitignored, loaded by python-dotenv)
├── ruff.toml                   Python linter/formatter config
├── _config.yml                 Jekyll config (GitHub Pages)
│
├── app/                        Web application
│   ├── Dockerfile              Multi-stage: node build → python serve
│   ├── backend/
│   │   ├── main.py             FastAPI app, SSE endpoint, static serving
│   │   ├── agent.py            Gemini agent loop (tool calling, streaming, 15-iter cap)
│   │   ├── tools.py            Tool wrappers + TOOL_REGISTRY + TOOL_DECLARATIONS
│   │   ├── steering.py         Tour-type detection → system prompt assembly
│   │   ├── i18n.py             Bilingual error messages (de/en)
│   │   └── pyproject.toml
│   └── frontend/
│       ├── src/
│       │   ├── App.vue         Root: SSE parsing, state, split-pane layout
│       │   ├── main.ts         Vue entry point
│       │   ├── i18n.ts         UI translations (de/en)
│       │   ├── style.css       Tailwind directives only
│       │   └── components/
│       │       ├── ChatInput.vue     Textarea + localStorage history dropdown
│       │       ├── TourContent.vue   Markdown → HTML (marked + DOMPurify)
│       │       └── TourMap.vue       Leaflet map (polyline + circle markers)
│       ├── vite.config.ts      Dev proxy /api → :8000
│       └── package.json
│
├── mcp/                        MCP servers — one directory per server
│   ├── brouter/                Cycling routing, geocoding, map + elevation rendering
│   ├── ors/                    Car/foot routing, isochrones, distance matrix
│   ├── osrm/                   Car routing + GPX export (no API key)
│   ├── open-meteo/             Weather forecast + geocoding
│   ├── vbb/                    Berlin/Brandenburg public transit
│   ├── overpass/               POI search along GPX routes (OSM)
│   ├── waymarkedtrails/        Marked hiking/cycling routes
│   ├── wikivoyage/             Travel guide articles (DE/EN)
│   ├── tavily/                 Web search
│   ├── travel-content/         Blog & video search
│   ├── serpapi-flights/        Google Flights search
│   ├── gitlab/                 GitLab (dev tool, disabled by default)
│   ├── jira/                   Jira (dev tool, disabled by default)
│   ├── sonarqube/              SonarQube (dev tool, disabled by default)
│   └── context7/               Library docs (disabled by default)
│
├── trips/                      Generated tour output (committed to repo)
│   ├── bike/
│   │   ├── README.md           Tour catalog
│   │   └── {tour-name}/
│   │       ├── index.md        Tour description (German)
│   │       ├── gpx/            GPX tracks
│   │       └── img/            Route map + elevation profile PNGs
│   ├── hike/
│   │   └── README.md
│   └── road/
│       ├── README.md           Trip catalog
│       └── {trip-name}/
│           ├── index.md        Trip description (German)
│           ├── review.md       Optional cross-LLM review
│           ├── gpx/            One GPX per driving day
│           └── img/            One route map per driving day
│
├── scripts/                    Standalone utilities
│   └── render_roadtrip_map.py
│
└── .kiro/
    ├── settings/mcp.json       MCP server registration + enable/disable flags
    └── steering/               System prompt fragments for the Gemini agent
        ├── user-preferences.md Always loaded — travel group, interests, food/hotel rules
        ├── bike-planner.md     Cycling tour workflow + BRouter/VBB rules
        ├── bike-template.md    Output template for cycling tours
        ├── road-planner.md     Roadtrip workflow + ORS/OSRM rules
        ├── road-template.md    Output template for road trips
        ├── app-development.md  Web app coding guidelines
        └── commit-messages.md  Conventional Commits rules
```

## MCP Server Layout

Each `mcp/<name>/` follows this pattern:

```
mcp/<name>/
├── server.py       FastMCP app + @mcp.tool() definitions, input validation
├── <name>.py       Pure async HTTP client logic (no FastMCP dependency)
├── pyproject.toml  Self-contained uv package (fastmcp + httpx + extras)
└── tests/          pytest + hypothesis tests
```

- `server.py` owns MCP protocol, validation, and response formatting
- `<name>.py` contains raw API calls — importable independently of FastMCP
- API keys: `load_dotenv(Path(__file__).parent.parent.parent / ".env")` at server startup
- Never add `"env"` blocks in `mcp.json` for keys that live in `.env`

## Naming Conventions

| Artifact                    | Convention                            |
| --------------------------- | ------------------------------------- |
| Python files                | `snake_case.py`                       |
| Vue components              | `PascalCase.vue`                      |
| TS utilities                | `camelCase.ts`                        |
| Tour/trip dirs, GPX, images | `kebab-case` (ASCII-safe: ü→ue, ö→oe) |
| MCP server dirs             | `kebab-case` matching server name     |

## Trip Output Structure

- Directory: `trips/{type}/{kebab-case-name}/`
- Main doc: `index.md` (German)
- GPX: `gpx/{segment-name}.gpx`
- Images: `img/{description}.png`
- Optional review: `review.md`

## Steering File Inclusion

YAML front matter controls when a steering file is loaded into the system prompt:

- No front matter → always included
- `inclusion: fileMatch` + `fileMatchPattern: 'trips/bike/**'` → loaded when a matching file is in context
- `inclusion: manual` → only when explicitly referenced with `#` in chat
