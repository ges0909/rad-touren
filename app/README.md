# Trip Planner App

AI-powered tour planner — FastAPI backend with Gemini agent + Vue 3 frontend.

## Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+ with npm
- Gemini API key from [Google AI Studio](https://aistudio.google.com)

## Setup

```bash
# Environment (project root)
echo "GEMINI_API_KEY=your-key" > .env

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

# Frontend (port 5173, proxies /api → backend)
cd app/frontend && npm run dev
```

Open http://localhost:5173.

## Production

```bash
# Docker
cd app && docker build -t trip-planner .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key trip-planner

# Without Docker
cd app/frontend && npm run build
cd app/backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Structure

```
app/
├── backend/
│   ├── main.py          # FastAPI app, SSE endpoint, static serving
│   ├── agent.py         # Gemini agent loop (tool calling, streaming)
│   ├── tools.py         # Tool wrappers + Gemini function declarations
│   ├── steering.py      # .kiro/steering/ → system prompt
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

Gemini acts as LLM orchestrator. The backend loads steering files (`.kiro/steering/`) as system instructions and registers MCP server functions as Gemini tools. The agent loop iterates: prompt → tool calls → results → final markdown response, streamed via SSE.

The frontend renders Markdown to HTML using [`marked`](https://github.com/markedjs/marked) with Tailwind Typography (`prose` classes) for styling. Routes and waypoints are displayed on a Leaflet map.
