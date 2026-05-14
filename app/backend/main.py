"""FastAPI backend for the Trip Planner web app."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from agent import create_client, run_agent

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

app = FastAPI(title="Trip Planner API")

# Gemini client (initialized on first request)
_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = create_client(api_key)
    return _client


# In-memory session storage (MVP)
sessions: dict[str, list[dict]] = {}


@app.post("/api/chat")
async def chat(request: Request):
    """Handle chat messages and stream responses via SSE."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    if not message:
        return {"error": "No message provided"}

    # Get or create session history
    if session_id not in sessions:
        sessions[session_id] = []

    chat_history = sessions[session_id]

    async def event_generator():
        try:
            client = get_client()
        except RuntimeError as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }
            return

        try:
            async for event in run_agent(
                client=client,
                user_message=message,
                chat_history=chat_history,
            ):
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"], ensure_ascii=False),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": f"Interner Fehler: {e!s}"},
                    ensure_ascii=False,
                ),
            }
            return

        # Save to history after completion
        chat_history.append({"role": "user", "content": message})

    return EventSourceResponse(event_generator())


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


# Serve frontend static files (production)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
