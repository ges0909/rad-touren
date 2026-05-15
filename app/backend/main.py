"""FastAPI backend for the Trip Planner web app."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from google import genai
from sse_starlette.sse import EventSourceResponse

from agent import create_client, run_agent
from i18n import msg

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

app = FastAPI(title="Trip Planner API")

# Gemini client (initialized on first request)
_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Get or create the Gemini client singleton."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = create_client(api_key)
    return _client


# In-memory session storage (MVP)
sessions: dict[str, list[dict[str, str]]] = {}


@app.post("/api/chat")
async def chat(request: Request) -> EventSourceResponse:
    """Handle chat messages and stream responses via SSE."""
    body: dict[str, Any] = await request.json()
    message: str = body.get("message", "")
    session_id: str = body.get("session_id", "default")
    language: str = body.get("language", "de")

    if not message:
        return {"error": "No message provided"}  # type: ignore[return-value]

    # Get or create session history
    if session_id not in sessions:
        sessions[session_id] = []

    chat_history: list[dict[str, str]] = sessions[session_id]

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        lang = language if language in ("de", "en") else "de"
        try:
            client = get_client()
        except RuntimeError:
            yield {
                "event": "error",
                "data": json.dumps({"error": msg("no_api_key", lang)}, ensure_ascii=False),
            }
            return

        try:
            async for event in run_agent(
                client=client,
                user_message=message,
                chat_history=chat_history,
                language=lang,
            ):
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"], ensure_ascii=False),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": msg("internal_error", lang, detail=str(e))},
                    ensure_ascii=False,
                ),
            }
            return

        # Save to history after completion
        chat_history.append({"role": "user", "content": message})

    return EventSourceResponse(event_generator())


@app.get("/api/health")
async def health() -> dict[str, Any]:
    """Health check endpoint."""
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


# Serve frontend static files (production)
FRONTEND_DIST: Path = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
