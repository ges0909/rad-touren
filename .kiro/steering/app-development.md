---
inclusion: fileMatch
fileMatchPattern: "app/**"
---

# App Development Guidelines

Rules for the Trip Planner web application (`app/` directory).

## Code Philosophy

- Simplicity and readability over complexity. No clever abstractions, premature optimization, or over-engineering.
- Short functions, clear names, minimal nesting. Fewer files and less indirection is better.
- Comments explain _why_, not _what_. If code needs a "what" comment, rewrite it.

## Architecture

Chat-based AI trip planner: user sends a travel request → backend runs a Gemini agent loop with tool calling → streams results via SSE → frontend renders Markdown + Leaflet map.

```
app/
├── backend/           # Python (FastAPI + Gemini agent)
│   ├── main.py        # FastAPI app, SSE endpoint, static file serving
│   ├── agent.py       # Gemini agent loop (tool calling, streaming SSE events)
│   ├── tools.py       # Tool wrappers + Gemini function declarations (TOOL_REGISTRY)
│   ├── steering.py    # Loads .kiro/steering/ files → assembles system prompt
│   ├── i18n.py        # Bilingual error messages (de/en), key-based lookup
│   └── pyproject.toml # Dependencies managed with uv
├── frontend/          # Vue 3 + TypeScript (Vite)
│   ├── src/
│   │   ├── App.vue          # Root: SSE parsing, state, split-pane layout
│   │   ├── main.ts          # Vue app entry point
│   │   ├── i18n.ts          # Frontend translations (de/en), key-based lookup
│   │   ├── style.css        # Tailwind directives only
│   │   └── components/
│   │       ├── ChatInput.vue    # Textarea + localStorage history dropdown
│   │       ├── TourContent.vue  # Markdown → HTML via `marked`
│   │       └── TourMap.vue      # Leaflet map (polyline + circle markers)
│   ├── vite.config.ts  # Dev proxy: /api → http://localhost:8000
│   └── tailwind.config.js
└── Dockerfile          # Multi-stage: node build → python serve
```

## Tech Stack

| Layer    | Technology                                                        |
| -------- | ----------------------------------------------------------------- |
| Frontend | Vue 3 Composition API (`<script setup>`), TypeScript              |
| Styling  | Tailwind CSS 3 + @tailwindcss/typography                          |
| Map      | Leaflet (vanilla JS, no vue-leaflet wrapper)                      |
| Bundler  | Vite 8                                                            |
| Backend  | Python 3.12+, FastAPI, uvicorn                                    |
| LLM      | Google Gemini 2.5 Flash via `google-genai` SDK                    |
| SSE      | `sse-starlette` (backend) → `fetch` + `ReadableStream` (frontend) |
| Packages | uv (backend), npm (frontend)                                      |

## Dev Workflow

```bash
# Backend
cd app/backend && uv run uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd app/frontend && npm run dev   # Vite on :5173, proxies /api → :8000

# Build check
cd app/frontend && npm run build  # vue-tsc --noEmit + vite build

# Tests
cd app/backend && uv run pytest
```

## Frontend Conventions

- Always `<script setup lang="ts">`. No Options API.
- Type props with `defineProps<{...}>()`, emits with `defineEmits<{...}>()`.
- State lives in `App.vue` via `ref()` / `reactive()`. No Pinia or Vuex.
- Tailwind utility classes only. No `<style>` blocks unless truly unavoidable.
- Components are single-file `.vue`. No separate `.ts` logic files per component.
- Use `computed()` for derived state, `watch()` / `watchEffect()` for side effects.
- SSE parsing in `App.vue` using `fetch` + `ReadableStream` — not EventSource.
- Leaflet used directly (no vue-leaflet wrapper). Map lifecycle via `onMounted` + `watch`.
- Use `^` (caret) ranges in `package.json`.

## Backend Conventions

- Type annotations on all functions and parameters (PEP 484 / PEP 695 `type` statements).
- Use `dict[str, Any]` not bare `dict`. Prefer `TypedDict` for known shapes.
- All I/O is `async`. Tool functions are async coroutines.
- Never let exceptions escape the SSE generator — catch and yield an `error` event.
- Tool wrappers in `tools.py` return structured dicts, never formatted strings.
- The agent loop in `agent.py` has a hard cap of 15 iterations.
- System prompt assembled at runtime in `steering.py` from `.kiro/steering/` markdown files (YAML front matter stripped).
- Use `>=` version constraints in `pyproject.toml`, not pinned versions.

## SSE Event Protocol

Events streamed from `POST /api/chat`:

| Event    | Data shape                                                       | When emitted                   |
| -------- | ---------------------------------------------------------------- | ------------------------------ |
| `status` | `{"message": string}`                                            | Before each tool execution     |
| `tour`   | `{"markdown": string}`                                           | Final LLM text response        |
| `map`    | `{"waypoints": [[lat,lng],...]}` or `{"route": [[lat,lng],...]}` | After geo tool returns results |
| `error`  | `{"error": string}`                                              | Any failure (user-facing text) |
| `done`   | `{"iterations": number}`                                         | Agent loop completed           |

Frontend parses by reading the stream line-by-line (lines starting with `data:`).

## Adding a New Tool

1. Write `async def tool_name(...)` in `tools.py` returning `dict[str, Any]`.
2. Add a Gemini `FunctionDeclaration` dict to `TOOL_DECLARATIONS` list.
3. Register in `TOOL_REGISTRY: dict[str, ToolFn]`.
4. If the tool returns geo data, emit `map` events in `agent.py` (follow `calculate_car_route` pattern).
5. MCP server code lives in `mcp/<server-name>/server.py` — import helpers from there via `sys.path` insertion.

## i18n Pattern

Both frontend and backend use the same pattern: a flat dict of message keys → `{de: ..., en: ...}` translations with `{placeholder}` interpolation.

- Backend: `i18n.py` exports `msg(key, lang, **kwargs)`. Add new keys to `MESSAGES` dict.
- Frontend: `i18n.ts` exports `t(key, lang, params?)`. Add new keys to `messages` object.
- Language is passed from the frontend via the `language` field in the `/api/chat` request body.
- All user-facing error messages must go through i18n — never hardcode strings.

## Logging

- `logging.getLogger(__name__)` per module. Never `print()`.
- `basicConfig(level=logging.INFO)` set once in `main.py`.
- Levels: DEBUG (tool args/results), INFO (requests, iterations), WARNING (retryable), ERROR (API failures), EXCEPTION (unexpected + stacktrace).
- Never log API keys or tokens.

## File Naming

- Backend: `snake_case.py`
- Frontend components: `PascalCase.vue`
- Frontend utilities: `camelCase.ts`
- GPX/map assets: `kebab-case`

## Error Handling

- Backend: wrap tool calls in try/except, return `{"error": "..."}` dict on failure. In the agent loop, catch `ClientError`/`ServerError` from Gemini and yield localized error events via `i18n.msg()`.
- Frontend: display `errorMessage` ref in a dismissible banner. Reset on new request.

## Testing

- Backend: `pytest` via `uv run pytest`. Use `httpx.AsyncClient` for endpoint tests.
- Frontend: no test framework. Manual testing via dev server.

## Environment

- `.env` at project root contains `GEMINI_API_KEY`. Loaded via `python-dotenv` in `main.py`.
- Never commit `.env` (listed in `.gitignore`).
- The Gemini client is a lazy singleton initialized on first request in `main.py`.
