"""Pure HTTP client logic for Tavily Search API.

No FastMCP dependency — importable independently for testing.
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com"


async def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = True,
) -> dict:
    """Search the web via Tavily.

    Returns raw API response as dict, or {"error": "..."} on failure.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}

    if not query or len(query.strip()) < 3:
        return {"error": "query must be at least 3 characters"}

    query = query.strip()[:400]
    max_results = max(1, min(10, max_results))

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TAVILY_BASE_URL}/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "include_answer": include_answer,
                    "include_raw_content": False,
                },
            )
    except httpx.TimeoutException:
        return {"error": "Request timed out"}

    if response.status_code != 200:
        return {"error": f"Tavily API returned {response.status_code}"}

    return response.json()


async def web_extract(url: str) -> dict:
    """Extract main content from a URL via Tavily.

    Returns raw API response as dict, or {"error": "..."} on failure.
    """
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}

    if not url or not url.startswith(("http://", "https://")):
        return {"error": "url must start with http:// or https://"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{TAVILY_BASE_URL}/extract",
                json={
                    "api_key": TAVILY_API_KEY,
                    "urls": [url],
                },
            )
    except httpx.TimeoutException:
        return {"error": "Request timed out"}

    if response.status_code != 200:
        return {"error": f"Tavily API returned {response.status_code}"}

    return response.json()
