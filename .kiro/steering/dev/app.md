---
inclusion: fileMatch
fileMatchPattern: ["app/**"]
---

# Gerrit on Tour — Web App Development

AI-powered tour planning platform. This document provides context for developing the web application (Vue 3 + FastAPI).

## Architecture Overview

**Two deployment modes:**

1. **Kiro-native workflow (primary)**
   - User opens project in Kiro
   - Types tour request in chat
   - MCP servers provide routing, weather, POIs, transit, travel content
   - Steering files guide the planning workflow
   - Results saved as Markdown + GPX under `trips/`

2. **Standalone web app**
   - Browser UI (Vue 3 + FastAPI)
   - Replicates the Gemini agent loop
   - Accessible without Kiro
   - SSE-based streaming responses

## Tech Stack

| Layer    | Technology                                             |
| -------- | ------------------------------------------------------ |
| Backend  | FastAPI + uvicorn, Google Gemini 2.5 Flash, SSE, httpx |
| Frontend | Vue 3 Composition API, Vite, Tailwind CSS, Leaflet     |
| Python   | 3.12+, managed by **uv**                               |
| Node     | 20+, managed by **npm**                                |
| Maps     | Leaflet (vanilla JS), BRouter tiles                    |
| AI       | Google Gemini 2.5 Flash (function calling + streaming) |

## Output Structure

Generated tours are committed to the repository:

```
trips/
├── bike/{tour-name}/
│   ├── index.md        # German-language tour description
│   ├── gpx/            # GPX track(s)
│   └── img/            # Route map + elevation profile PNGs
└── road/{trip-name}/
    ├── index.md        # German-language trip description
    ├── review.md       # Optional cross-LLM review
    ├── gpx/            # One GPX per driving day
    └── img/            # One route map per driving day
```

## Development Workflows

### Running the App Locally

```bash
# Backend
cd app/backend && uv run uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd app/frontend && npm run dev  # Vite on :5173, proxies /api → :8000
```

### Building for Deployment

```bash
cd app && docker build -t gerrit-on-tour .
# Multi-stage: node build → python serve
```

## Key Design Principles

1. **Simplicity over abstraction** — clear code, minimal indirection
2. **Steering-driven behavior** — tour-type-specific workflows via fileMatch patterns
3. **Gemini function calling** — structured tool use, 15-iteration cap
4. **Output reproducibility** — all generated tours committed to git

## Naming Conventions

| Artifact                    | Convention                            |
| --------------------------- | ------------------------------------- |
| Python files                | `snake_case.py`                       |
| Vue components              | `PascalCase.vue`                      |
| TS utilities                | `camelCase.ts`                        |
| Tour/trip dirs, GPX, images | `kebab-case` (ASCII-safe: ü→ue, ö→oe) |

## Project Goals

**Current (Personal Use):**

- Plan and document personal bike/car trips from Berlin/Brandenburg
- Experiment with AI-assisted tour planning workflows

**Future (Platform):**

- Generalize for other users/regions
- Add collaborative features (shared trips, reviews)
- Implement trip booking integrations
- Mobile app (React Native or PWA)

## Related Documentation

- **MCP development:** `mcp-development.md` (MCP server structure and patterns)
- **User-facing behavior:** `user-preferences.md` (trips context only)
