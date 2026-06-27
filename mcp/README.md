# MCP Servers

Custom [Model Context Protocol](https://modelcontextprotocol.io/) servers for this project. All servers use [FastMCP](https://github.com/jlowin/fastmcp) + [httpx](https://www.python-httpx.org/) and are launched via `uv run`.

## Configuration

- **MCP registration**: `.kiro/settings/mcp.json`
- **API keys**: `.env` at project root (gitignored)
- **Python**: ≥ 3.11, managed via [uv](https://docs.astral.sh/uv/)

Each server is self-contained with its own `pyproject.toml`. Install all at once from project root:

```bash
uv sync --all-packages
```

---

## Active Servers

| Server               | Directory              | Description                                                         | External API                                               |
| -------------------- | ---------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------- |
| **BRouter**          | `mcp/brouter/`         | Cycling routing, GPX map & elevation profile rendering              | [brouter.de](https://brouter.de) + Nominatim               |
| **Open-Meteo**       | `mcp/open-meteo/`      | Weather forecast & geocoding                                        | [open-meteo.com](https://open-meteo.com)                   |
| **VBB**              | `mcp/vbb/`             | Public transport Berlin/Brandenburg (stops, departures, journeys)   | [v6.vbb.transport.rest](https://v6.vbb.transport.rest)     |
| **Overpass**         | `mcp/overpass/`        | POI search along GPX routes (food, art, swimming…)                  | [Overpass API](https://overpass-api.de)                    |
| **OpenRouteService** | `mcp/ors/`             | Car/foot routing, geocoding, isochrones, distance matrix            | [openrouteservice.org](https://openrouteservice.org)       |
| **OSRM**             | `mcp/osrm/`            | Car routing & GPX export (no API key required)                      | [router.project-osrm.org](https://router.project-osrm.org) |
| **Wikivoyage**       | `mcp/wikivoyage/`      | Travel guide articles & sections (DE/EN)                            | [Wikivoyage API](https://de.wikivoyage.org)                |
| **Waymarked Trails** | `mcp/waymarkedtrails/` | Search official hiking/cycling routes & get details                 | [waymarkedtrails.org](https://waymarkedtrails.org)         |
| **SerpAPI Flights**  | `mcp/serpapi-flights/` | Flight search via Google Flights — prices, schedules, booking links | [serpapi.com](https://serpapi.com)                         |
| **Tavily**           | `mcp/tavily/`          | Web search & content extraction                                     | [tavily.com](https://tavily.com)                           |
| **Travel Content**   | `mcp/travel-content/`  | Quality travel journalism search + route tip extraction             | [tavily.com](https://tavily.com) (curated sources)         |
| **Travel Videos**    | `mcp/travel-videos/`   | Public broadcaster video search + YouTube transcripts               | YouTube (ÖR channels)                                      |
| **Podcasts**         | `mcp/podcasts/`        | Travel podcast search + episode transcript extraction               | [iTunes Search API](https://itunes.apple.com) (no key)     |

---

## Authentication

All API keys are stored in **`.env` at the project root** (gitignored). Each server's client module loads this file at startup via `load_dotenv()` — keys are never passed through `mcp.json`.

| Variable          | Server                  | Where to get it                                                   |
| ----------------- | ----------------------- | ----------------------------------------------------------------- |
| `ORS_API_KEY`     | OpenRouteService        | [openrouteservice.org](https://openrouteservice.org/dev/#/signup) |
| `TAVILY_API_KEY`  | Tavily / Travel Content | [tavily.com](https://tavily.com)                                  |
| `SERPAPI_API_KEY` | SerpAPI Flights         | [serpapi.com](https://serpapi.com)                                |

BRouter, Open-Meteo, VBB, Overpass, OSRM, Wikivoyage, Waymarked Trails, Travel Videos, and Podcasts use free public APIs with no key required.

### Why no `"env"` blocks in mcp.json

Kiro expands `${VAR}` in `mcp.json` only from the **system environment**, not from `.env`. If a key is only in `.env` (not exported to the shell), the server would receive the literal string `"${VAR}"` — an invalid key. Instead, every client module calls:

```python
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
```

**Rule:** Never add `"env"` blocks in `mcp.json` for keys that live in `.env`.

---

## Enabling / Disabling Servers

Set `"disabled": true/false` per server in `.kiro/settings/mcp.json`.

---

## Server Structure

Every server follows this layout:

```
mcp/<name>/
├── server.py       # FastMCP app, @mcp.tool() declarations, response formatting
├── <name>.py       # Pure async HTTP client (no FastMCP dep, importable independently)
├── pyproject.toml  # Self-contained uv package
└── tests/          # pytest + pytest-asyncio tests
```

- **`server.py`** — MCP protocol layer: validation, tool declarations, formatting results as strings. No direct HTTP calls.
- **`<name>.py`** — HTTP client: async functions returning raw dicts. Returns `{"error": "..."}` on failure.

---

## Adding a New Server

1. Create `mcp/<name>/` directory.
2. Add `pyproject.toml` with at minimum `fastmcp` and `httpx` as dependencies.
3. Write `<name>.py` with async functions that call the external API and return dicts.
4. Write `server.py` with `FastMCP("<Name>")`, `@mcp.tool()` functions, and `if __name__ == "__main__": mcp.run()`.
5. Add entry to `.kiro/settings/mcp.json`:
   ```json
   "<name>": {
     "command": "uv",
     "args": ["run", "--directory", "mcp/<name>", "python", "server.py"],
     "disabled": false,
     "autoApprove": ["tool_name"]
   }
   ```

See any existing server (e.g. `mcp/ors/`) as a reference implementation.
