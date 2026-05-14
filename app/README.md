# Trip Planner Web App

AI-powered tour planner — FastAPI backend with Gemini agent + Vue 3 frontend.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Node.js 20+
- npm

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-api-key-here
```

Get a free API key from [Google AI Studio](https://aistudio.google.com).

### 2. Backend

```bash
cd app/backend
uv sync
```

### 3. Frontend

```bash
cd app/frontend
npm install
```

## Local Development

Run both services in separate terminals:

**Terminal 1 — Backend (port 8000):**

```bash
cd app/backend
uv run uvicorn main:app --reload
```

**Terminal 2 — Frontend (port 5173):**

```bash
cd app/frontend
npm run dev
```

The Vite dev server proxies `/api/*` requests to the backend automatically.

Open http://localhost:5173 in the browser.

## Production Build

### With Docker

```bash
cd app
docker build -t trip-planner .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key trip-planner
```

### Without Docker

```bash
# Build frontend
cd app/frontend
npm run build

# Start backend (serves frontend from dist/)
cd app/backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
app/
├── backend/
│   ├── main.py          # FastAPI app, SSE streaming, static file serving
│   ├── agent.py         # Gemini agent loop with tool calling
│   ├── tools.py         # MCP functions as Gemini tool declarations
│   ├── steering.py      # Load .kiro/steering/ files as system prompt
│   └── pyproject.toml   # Dependencies (managed with uv)
├── frontend/
│   ├── src/
│   │   ├── App.vue      # Main layout (chat + map + tour)
│   │   └── components/  # ChatInput, TourMap, TourContent
│   ├── package.json
│   └── vite.config.ts   # Dev proxy to backend
├── Dockerfile           # Multi-stage: build frontend, serve via FastAPI
└── README.md            # This file
```

## API Endpoints

| Method | Path          | Description                     |
| ------ | ------------- | ------------------------------- |
| POST   | `/api/chat`   | Send prompt, receive SSE stream |
| GET    | `/api/health` | Health check                    |

## Architecture

The backend uses Google Gemini as an LLM orchestrator. It loads the project's steering files (`.kiro/steering/`) as system instructions and registers MCP server functions as Gemini tools. The agent loop iterates: prompt → tool calls → results → next call → final markdown response, streamed to the frontend via Server-Sent Events.
