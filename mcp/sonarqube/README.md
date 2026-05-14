# SonarQube MCP Server

MCP server for accessing a self-hosted SonarQube instance via Personal Access Token.

## Setup

1. Create a Personal Access Token in SonarQube:
   - My Account → Security → Generate Tokens
   - Type: User Token

2. Configure environment variables in `.env`:

   ```
   SONARQUBE_URL=https://sonarqube.your-company.com
   SONARQUBE_TOKEN=squ_xxxxxxxxxxxxxxxxxxxx
   ```

3. Install dependencies:

   ```bash
   cd mcp/sonarqube
   uv sync
   ```

4. Enable in `.kiro/settings/mcp.json` by setting `"disabled": false`

## Tools

| Tool                     | Description                               |
| ------------------------ | ----------------------------------------- |
| `list_projects`          | List SonarQube projects                   |
| `get_project_status`     | Quality gate status + key metrics         |
| `list_issues`            | List bugs, vulnerabilities, code smells   |
| `get_issue`              | Detailed issue info with rule description |
| `list_hotspots`          | List security hotspots                    |
| `get_measures_history`   | Metrics trend over last analyses          |
| `get_duplications`       | Code duplication blocks in a file         |
| `get_source_with_issues` | Source code with issue annotations        |

## Authentication

Uses HTTP Basic Auth with the token as username and empty password,
which is the standard SonarQube token authentication method.
SSL verification is disabled (`verify=False`) for self-signed certificates.

## Useful Filters

### Severities

`BLOCKER`, `CRITICAL`, `MAJOR`, `MINOR`, `INFO`

### Types

`BUG`, `VULNERABILITY`, `CODE_SMELL`, `SECURITY_HOTSPOT`

### Statuses

`OPEN`, `CONFIRMED`, `REOPENED`, `RESOLVED`, `CLOSED`
