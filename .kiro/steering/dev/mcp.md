---
inclusion: fileMatch
fileMatchPattern: ["mcp/**"]
---

# MCP Server Development Guide

Guidelines for developing MCP servers in this project.

## Tech Stack

| Component | Technology                                                          |
| --------- | ------------------------------------------------------------------- |
| Framework | FastMCP + httpx                                                     |
| Python    | 3.12+, managed by **uv**                                            |
| Transport | stdio JSON-RPC subprocess                                           |
| Testing   | pytest + pytest-asyncio, hypothesis for property-based tests, respx |

## Code Quality

Ruff (`ruff.toml` at project root):

- Target: Python 3.12, line-length 100, double quotes
- Rules: E, F, I, UP, B, SIM (E501 ignored — formatter handles line length)

Run: `uvx ruff check mcp/` and `uvx ruff format mcp/`

## Common Commands

```bash
cd mcp/<name> && uv sync                # install dependencies
cd mcp/<name> && uv run pytest          # run tests
cd mcp/<name> && uv run python server.py  # run server locally
```

## Environment Variables

All keys in `.env` at project root (gitignored). MCP servers load via `python-dotenv`. Never add `"env"` blocks to `mcp.json`.

| Variable          | Used by                     |
| ----------------- | --------------------------- |
| `ORS_API_KEY`     | OpenRouteService MCP        |
| `TAVILY_API_KEY`  | Tavily / Travel Content MCP |
| `SERPAPI_API_KEY` | SerpAPI Flights MCP         |

## Existing MCP Servers

| Server            | Purpose                              | API Key Required |
| ----------------- | ------------------------------------ | ---------------- |
| `brouter`         | Cycling routing + elevation profiles | No               |
| `ors`             | Car/foot routing + isochrones        | Yes              |
| `osrm`            | Car routing (OpenStreetMap)          | No               |
| `open-meteo`      | Weather forecasts                    | No               |
| `vbb`             | Berlin/Brandenburg public transit    | No               |
| `overpass`        | POI search along routes (OSM)        | No               |
| `wikivoyage`      | Travel guide articles                | No               |
| `waymarkedtrails` | Marked hiking/cycling routes         | No               |
| `tavily`          | Web search                           | Yes              |
| `travel-content`  | Travel blog/video search             | Yes              |
| `serpapi-flights` | Google Flights search                | Yes              |
| `podcasts`        | Travel podcast search + transcripts  | No               |

## Naming Convention

Server directories use `kebab-case` matching the server name (e.g., `mcp/open-meteo/`, `mcp/serpapi-flights/`).

## Architecture

### File Layout

```
mcp/<name>/
├── server.py       # FastMCP app, @mcp.tool() declarations, input validation, response formatting
├── <name>.py       # Pure async HTTP client (no FastMCP dependency), returns dicts
├── pyproject.toml  # Self-contained uv package
└── tests/          # pytest + pytest-asyncio + respx/hypothesis
```

### Separation of Concerns

- **`server.py`** — MCP protocol layer. Declares tools, validates inputs, formats raw data into human-readable strings. No direct HTTP calls to external APIs.
- **`<name>.py`** — Pure HTTP client. Async functions calling external APIs, returning raw dicts. Returns `{"error": "..."}` on failure. Importable independently for testing.

### Key Rules

1. Every `server.py` ends with `if __name__ == "__main__": mcp.run()`
2. Start command: `uv run --directory mcp/<name> python server.py` (never `fastmcp run`)
3. `load_dotenv` lives in the client module (`<name>.py`), not `server.py`. Path: `Path(__file__).resolve().parent.parent.parent / ".env"`
4. Add `python-dotenv` to `pyproject.toml` only if the server requires API keys
5. Error pattern: modules return `{"error": "message"}`; `server.py` checks and formats as user-facing string
6. Import convention in `server.py`: `from <module> import func as _func` (underscore-prefixed alias)
7. Every `@mcp.tool()` function has a docstring with `Args:` section (LLM reads these for parameter understanding)
8. Tool return type is always `str` — format output as Markdown for readability

### server.py Pattern

```python
"""MCP server wrapping <API name> for <purpose>."""

from fastmcp import FastMCP
from <module> import some_function as _some_function

mcp = FastMCP("<Server Display Name>")


@mcp.tool()
async def some_tool(param: str) -> str:
    """Tool description for the LLM.

    Args:
        param: Parameter description.
    """
    data = await _some_function(param)
    if "error" in data:
        return f"Error: {data['error']}"
    # Format data into readable Markdown string
    return "..."


if __name__ == "__main__":
    mcp.run()
```

### Client Module Pattern (`<name>.py`)

```python
"""Pure HTTP client logic for <API name>."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

API_KEY = os.getenv("<ENV_VAR_NAME>", "")
BASE_URL = "https://api.example.com"


async def some_function(param: str) -> dict:
    """Returns raw API response as dict, or {"error": "..."} on failure."""
    if not API_KEY:
        return {"error": "<ENV_VAR_NAME> not configured"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/endpoint", params={"q": param})

    if response.status_code != 200:
        return {"error": f"API returned {response.status_code}"}

    return response.json()
```

### pyproject.toml Pattern

```toml
[project]
name = "<name>-mcp"
version = "1.0.0"
description = "MCP server wrapping <API> for <purpose>"
requires-python = ">=3.11"
dependencies = [
    "fastmcp",
    "httpx",
    # "python-dotenv",  # only if API key needed
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "respx",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
```

### mcp.json Registration

```json
"<name>": {
  "command": "uv",
  "args": ["run", "--directory", "mcp/<name>", "python", "server.py"],
  "disabled": false,
  "autoApprove": ["tool_name_1", "tool_name_2"]
}
```

### Input Validation Pattern

Validate inputs at the top of each tool function before calling the client module. Return descriptive error strings immediately on invalid input — do not raise exceptions.

```python
if len(waypoints) < 2:
    return "Error: at least 2 waypoints required."
if profile not in VALID_PROFILES:
    return f"Error: invalid profile '{profile}'. Valid: {', '.join(sorted(VALID_PROFILES))}"
```
