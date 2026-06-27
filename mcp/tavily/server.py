"""MCP server wrapping the Tavily Search API for web search.

Provides web search and content extraction tools for the trip planner agent.
Requires TAVILY_API_KEY environment variable.

Usage:
    python server.py
"""

from fastmcp import FastMCP
from tavily import web_extract as _web_extract
from tavily import web_search as _web_search

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
    data = await _web_search(query, max_results, search_depth, include_answer)

    if "error" in data:
        return f"Error: {data['error']}"

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
    data = await _web_extract(url)

    if "error" in data:
        return f"Error: {data['error']}"

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
