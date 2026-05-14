# MCP Servers

Custom [Model Context Protocol](https://modelcontextprotocol.io/) servers for this project. All servers use [FastMCP](https://github.com/jlowin/fastmcp) + [httpx](https://www.python-httpx.org/) and are launched via `uv run`.

## Configuration

- **MCP registration**: `.kiro/settings/mcp.json`
- **Environment variables / tokens**: `.env` (project root, not committed)
- **Python**: ≥ 3.11, managed via [uv](https://docs.astral.sh/uv/)

Each server has its own `pyproject.toml` and `.venv`. Setup:

```bash
cd mcp/<server-name>
uv sync
```

---

## Tour Planning & Routing

| Server               | Directory              | Description                                                       | External API                                               |
| -------------------- | ---------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| **BRouter**          | `mcp/brouter/`         | Bicycle routing, GPX map & elevation profile rendering            | [brouter.de](https://brouter.de) + Nominatim               |
| **Open-Meteo**       | `mcp/open-meteo/`      | Weather forecast & geocoding                                      | [open-meteo.com](https://open-meteo.com)                   |
| **VBB**              | `mcp/vbb/`             | Public transport Berlin/Brandenburg (stops, departures, journeys) | [v6.vbb.transport.rest](https://v6.vbb.transport.rest)     |
| **Overpass**         | `mcp/overpass/`        | POI search along GPX routes (food, art, swimming…)                | [Overpass API](https://overpass-api.de)                    |
| **OpenRouteService** | `mcp/ors/`             | Car/foot routing, geocoding, isochrones, distance matrix          | [openrouteservice.org](https://openrouteservice.org)       |
| **OSRM**             | `mcp/osrm/`            | Car routing & GPX export (no API key required)                    | [router.project-osrm.org](https://router.project-osrm.org) |
| **Wikivoyage**       | `mcp/wikivoyage/`      | Travel guide articles & sections (DE/EN)                          | [Wikivoyage API](https://de.wikivoyage.org)                |
| **Waymarked Trails** | `mcp/waymarkedtrails/` | Search official hiking/cycling routes & get details               | [waymarkedtrails.org](https://waymarkedtrails.org)         |

## Development Tools

| Server         | Directory        | Description                                                | Auth                  |
| -------------- | ---------------- | ---------------------------------------------------------- | --------------------- |
| **GitLab**     | `mcp/gitlab/`    | Projects, merge requests, pipelines, issues, code search   | `PRIVATE-TOKEN` (PAT) |
| **Jira Cloud** | `mcp/jira/`      | JQL search, issues, sprints, boards, comments, transitions | `Bearer` token (PAT)  |
| **SonarQube**  | `mcp/sonarqube/` | Quality gate, issues, hotspots, metrics, duplications      | Basic auth (token)    |

## Other

| Server       | Directory       | Description                     | Status   |
| ------------ | --------------- | ------------------------------- | -------- |
| **Context7** | `mcp/context7/` | Library documentation on-demand | disabled |

---

## Authentication

Servers requiring API keys or tokens read their credentials from environment variables:

| Variable          | Server           | Example                         |
| ----------------- | ---------------- | ------------------------------- |
| `ORS_API_KEY`     | OpenRouteService | `eyJvcm...`                     |
| `GITLAB_URL`      | GitLab           | `https://gitlab.company.com`    |
| `GITLAB_TOKEN`    | GitLab           | `glpat-xxxx`                    |
| `JIRA_URL`        | Jira             | `https://company.atlassian.net` |
| `JIRA_TOKEN`      | Jira             | PAT from Atlassian account      |
| `JIRA_EMAIL`      | Jira             | `user@company.com`              |
| `SONARQUBE_URL`   | SonarQube        | `https://sonar.company.com`     |
| `SONARQUBE_TOKEN` | SonarQube        | `squ_xxxx`                      |

---

## Enabling / Disabling Servers

Set `"disabled": true/false` per server in `.kiro/settings/mcp.json`. The corporate servers (GitLab, Jira, SonarQube) are disabled by default and must be enabled manually after configuring tokens.

---

## Adding a New Server

1. Create directory: `mcp/<name>/`
2. Add `pyproject.toml` with `fastmcp` + `httpx` as dependencies
3. Write `server.py` with `FastMCP("<Name>")` and `@mcp.tool()` functions
4. Run `uv sync` in the directory
5. Add entry to `.kiro/settings/mcp.json`
6. Optional: add `README.md` in the server directory
