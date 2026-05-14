"""MCP server for Context7 — up-to-date library documentation for LLMs.

Provides two tools:
1. resolve_library_id — search for a library by name
2. get_library_docs — fetch documentation for a specific library + query

Requires CONTEXT7_API_KEY environment variable (get from https://context7.com).

Usage:
    fastmcp run server.py
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

mcp = FastMCP("Context7 Documentation")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("CONTEXT7_API_KEY", "")
BASE_URL = "https://context7.com/api/v2"


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


async def _api_get(path: str, params: dict) -> dict | str:
    """Make authenticated GET request to Context7 API."""
    if not API_KEY:
        return (
            "Error: CONTEXT7_API_KEY environment variable not set. "
            "Get your key from https://context7.com"
        )

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"Authorization": f"Bearer {API_KEY}"},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return f"Context7 API error {e.response.status_code}: {e.response.text[:300]}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def resolve_library_id(
    library_name: str,
    query: str | None = None,
) -> str:
    """Search for a library by name and return matching Context7 library IDs.

    Use this to find the correct library ID before calling get_library_docs.

    Args:
        library_name: Library or package name to search for (e.g. "react", "fastapi", "pandas").
        query: Optional context query to improve relevance ranking (e.g. "state management with hooks").
    """
    params = {"libraryName": library_name}
    if query:
        params["query"] = query

    data = await _api_get("/libs/search", params)

    if isinstance(data, str):
        return data

    results = data.get("results", [])
    if not results:
        return f"No libraries found for '{library_name}'."

    lines = [f"Found {len(results)} library/libraries:\n"]
    for lib in results[:10]:
        lib_id = lib.get("id", "?")
        title = lib.get("title", "?")
        desc = lib.get("description", "")[:100]
        snippets = lib.get("totalSnippets", 0)
        trust = lib.get("trustScore", 0)
        versions = lib.get("versions", [])

        lines.append(f"- **{title}** — ID: `{lib_id}`")
        if desc:
            lines.append(f"  {desc}")
        lines.append(f"  Snippets: {snippets} | Trust: {trust}")
        if versions:
            lines.append(f"  Versions: {', '.join(versions[:5])}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_library_docs(
    library_id: str,
    query: str,
    tokens: int = 5000,
) -> str:
    """Fetch up-to-date documentation for a library from Context7.

    Call resolve_library_id first to get the library_id.

    Args:
        library_id: Context7 library ID (e.g. "/facebook/react", "/tiangolo/fastapi").
        query: What you want to know (e.g. "How to use dependency injection").
        tokens: Maximum number of tokens to return (default 5000).
    """
    params = {
        "libraryId": library_id,
        "query": query,
        "type": "txt",
        "tokens": str(tokens),
    }

    data = await _api_get("/context", params)

    if isinstance(data, str):
        # Plain text response or error
        return data

    # If JSON response, format it
    if isinstance(data, dict):
        code_snippets = data.get("codeSnippets", [])
        info_snippets = data.get("infoSnippets", [])

        lines = []
        for snippet in info_snippets:
            breadcrumb = snippet.get("breadcrumb", "")
            content = snippet.get("content", "")
            if breadcrumb:
                lines.append(f"### {breadcrumb}\n")
            lines.append(content)
            lines.append("")

        for snippet in code_snippets:
            title = snippet.get("codeTitle", "")
            desc = snippet.get("codeDescription", "")
            if title:
                lines.append(f"### {title}")
            if desc:
                lines.append(f"{desc}\n")
            for code_block in snippet.get("codeList", []):
                lang = code_block.get("language", "")
                code = code_block.get("code", "")
                lines.append(f"```{lang}")
                lines.append(code)
                lines.append("```\n")

        return "\n".join(lines) if lines else "No documentation found for this query."

    return str(data)
