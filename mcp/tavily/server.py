"""MCP server wrapping the Tavily Search API for web search.

Provides web search and content extraction tools for the trip planner agent.
Requires TAVILY_API_KEY environment variable.
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com"

mcp = FastMCP("Tavily Web Search")


@mcp.tool()
async def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_answer: bool = True,
) -> str:
    """Search the web for current information using Tavily.

    Best for: current events, restaurant reviews, travel tips, opening hours,
    prices, local recommendations, and anything not in your training data.

    Args:
        query: Search query (max 400 chars). Be specific for better results.
               Examples: "best restaurants Palermo Sicily 2025",
               "bike rental Berlin Kreuzberg", "ferry schedule Sardinia"
        max_results: Number of results to return (1-10, default 5)
        search_depth: "basic" (fast, default) or "advanced" (slower, more thorough)
        include_answer: Whether to include an AI-generated summary (default True)
    """
    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY not configured"

    if not query or len(query.strip()) < 3:
        return "Error: query must be at least 3 characters"

    query = query.strip()[:400]
    max_results = max(1, min(10, max_results))

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

    if response.status_code != 200:
        return f"Error: Tavily API returned {response.status_code}"

    data = response.json()

    lines: list[str] = []

    # AI-generated answer summary
    answer = data.get("answer")
    if answer:
        lines.append(f"**Zusammenfassung:** {answer}\n")

    # Individual results
    results = data.get("results", [])
    if results:
        lines.append(f"**Quellen ({len(results)}):**\n")
        for r in results:
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            content = r.get("content", "")
            # Truncate long content snippets
            if len(content) > 300:
                content = content[:300] + "..."
            lines.append(f"- **{title}**")
            if content:
                lines.append(f"  {content}")
            if url:
                lines.append(f"  → {url}")
            lines.append("")

    if not lines:
        return f"Keine Ergebnisse für: {query}"

    return "\n".join(lines)


@mcp.tool()
async def web_extract(url: str) -> str:
    """Extract the main content from a specific URL.

    Use this after web_search to get more details from a specific page.

    Args:
        url: Full URL to extract content from (must start with http:// or https://)
    """
    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY not configured"

    if not url or not url.startswith(("http://", "https://")):
        return "Error: url must start with http:// or https://"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{TAVILY_BASE_URL}/extract",
            json={
                "api_key": TAVILY_API_KEY,
                "urls": [url],
            },
        )

    if response.status_code != 200:
        return f"Error: Tavily API returned {response.status_code}"

    data = response.json()
    results = data.get("results", [])

    if not results:
        return f"Konnte keinen Inhalt extrahieren von: {url}"

    result = results[0]
    raw_content = result.get("raw_content", "")

    # Truncate very long content
    max_chars = 10000
    if len(raw_content) > max_chars:
        raw_content = raw_content[:max_chars] + "\n\n[... Inhalt gekürzt]"

    return f"# Inhalt von {url}\n\n{raw_content}"


if __name__ == "__main__":
    mcp.run()
