"""MCP server for SonarQube API access.

Provides tools for interacting with a self-hosted SonarQube instance
via personal access token authentication.
"""

import os
from urllib.parse import urlencode

import httpx
from fastmcp import FastMCP

mcp = FastMCP("SonarQube")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SONARQUBE_URL = os.environ.get("SONARQUBE_URL", "").rstrip("/")
SONARQUBE_TOKEN = os.environ.get("SONARQUBE_TOKEN", "")


def _auth() -> tuple[str, str]:
    """Return basic auth tuple (token as username, empty password)."""
    return (SONARQUBE_TOKEN, "")


def _check_config() -> str | None:
    """Return error message if configuration is missing."""
    if not SONARQUBE_URL:
        return "Error: SONARQUBE_URL environment variable is not set."
    if not SONARQUBE_TOKEN:
        return "Error: SONARQUBE_TOKEN environment variable is not set."
    return None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def _get(path: str, params: dict | None = None) -> dict | list | str:
    """Send GET request to SonarQube API. Returns parsed JSON or error string."""
    err = _check_config()
    if err:
        return err
    url = f"{SONARQUBE_URL}/api{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.get(url, auth=_auth(), params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"SonarQube API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"SonarQube connection error: {exc}"


async def _post(path: str, params: dict | None = None) -> dict | str:
    """Send POST request to SonarQube API."""
    err = _check_config()
    if err:
        return err
    url = f"{SONARQUBE_URL}/api{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.post(url, auth=_auth(), params=params)
            resp.raise_for_status()
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"SonarQube API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"SonarQube connection error: {exc}"


# ---------------------------------------------------------------------------
# Severity / Type formatting
# ---------------------------------------------------------------------------

_SEVERITY_EMOJI = {
    "BLOCKER": "🔴",
    "CRITICAL": "🟠",
    "MAJOR": "🟡",
    "MINOR": "🔵",
    "INFO": "⚪",
}

_TYPE_LABEL = {
    "BUG": "Bug",
    "VULNERABILITY": "Vulnerability",
    "CODE_SMELL": "Code Smell",
    "SECURITY_HOTSPOT": "Security Hotspot",
}


# ---------------------------------------------------------------------------
# MCP Tools — Projects
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_projects(
    search: str = "",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List SonarQube projects.

    Args:
        search: Filter projects by name or key (optional).
        per_page: Number of results per page (1-500, default: 20).
        page: Page number (default: 1).

    Returns:
        List of projects with key, name, and last analysis date.
    """
    params: dict[str, str] = {"ps": str(min(per_page, 500)), "p": str(page)}
    if search:
        params["q"] = search

    result = await _get("/projects/search", params)
    if isinstance(result, str):
        return result

    components = result.get("components", [])
    if not components:
        return "No projects found."

    paging = result.get("paging", {})
    total = paging.get("total", 0)

    lines = [f"## SonarQube Projects ({len(components)} of {total})\n"]
    for p in components:
        last_analysis = p.get("lastAnalysisDate", "never")[:16] if p.get("lastAnalysisDate") else "never"
        lines.append(
            f"- **{p['name']}**\n"
            f"  Key: `{p['key']}` | Last analysis: {last_analysis}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Project Status & Metrics
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_project_status(project_key: str) -> str:
    """Get the quality gate status and key metrics of a project.

    Args:
        project_key: SonarQube project key (e.g. "my-org:my-project").

    Returns:
        Quality gate status and metric values.
    """
    # Quality gate status
    qg_result = await _get("/qualitygates/project_status", {"projectKey": project_key})
    if isinstance(qg_result, str):
        return qg_result

    qg = qg_result.get("projectStatus", {})
    qg_status = qg.get("status", "UNKNOWN")
    qg_emoji = "✅" if qg_status == "OK" else "❌" if qg_status == "ERROR" else "⚠️"

    # Key metrics
    metric_keys = (
        "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,"
        "ncloc,sqale_rating,reliability_rating,security_rating,"
        "security_hotspots,alert_status"
    )
    metrics_result = await _get(
        "/measures/component",
        {"component": project_key, "metricKeys": metric_keys},
    )
    if isinstance(metrics_result, str):
        return f"{qg_emoji} Quality Gate: {qg_status}\n\n(Metrics unavailable: {metrics_result})"

    measures = metrics_result.get("component", {}).get("measures", [])
    metrics_map = {m["metric"]: m.get("value", "—") for m in measures}

    # Rating conversion (1=A, 2=B, 3=C, 4=D, 5=E)
    def _rating(val: str) -> str:
        try:
            return chr(64 + int(float(val)))  # 1→A, 2→B, etc.
        except (ValueError, TypeError):
            return val

    return (
        f"## {project_key}\n\n"
        f"{qg_emoji} **Quality Gate: {qg_status}**\n\n"
        f"### Metrics\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Lines of Code | {metrics_map.get('ncloc', '—')} |\n"
        f"| Bugs | {metrics_map.get('bugs', '—')} |\n"
        f"| Vulnerabilities | {metrics_map.get('vulnerabilities', '—')} |\n"
        f"| Security Hotspots | {metrics_map.get('security_hotspots', '—')} |\n"
        f"| Code Smells | {metrics_map.get('code_smells', '—')} |\n"
        f"| Coverage | {metrics_map.get('coverage', '—')}% |\n"
        f"| Duplications | {metrics_map.get('duplicated_lines_density', '—')}% |\n"
        f"| Reliability Rating | {_rating(metrics_map.get('reliability_rating', '—'))} |\n"
        f"| Security Rating | {_rating(metrics_map.get('security_rating', '—'))} |\n"
        f"| Maintainability Rating | {_rating(metrics_map.get('sqale_rating', '—'))} |\n"
    )


# ---------------------------------------------------------------------------
# MCP Tools — Issues
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_issues(
    project_key: str,
    severities: str = "",
    types: str = "",
    statuses: str = "OPEN,CONFIRMED,REOPENED",
    branch: str = "",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List SonarQube issues (bugs, vulnerabilities, code smells) for a project.

    Args:
        project_key: SonarQube project key.
        severities: Comma-separated severity filter: BLOCKER, CRITICAL, MAJOR,
            MINOR, INFO (optional, shows all if empty).
        types: Comma-separated type filter: BUG, VULNERABILITY, CODE_SMELL,
            SECURITY_HOTSPOT (optional).
        statuses: Comma-separated status filter (default: "OPEN,CONFIRMED,REOPENED").
        branch: Branch name to filter (optional, uses main branch if empty).
        per_page: Results per page (1-500, default: 20).
        page: Page number (default: 1).

    Returns:
        Formatted list of issues with severity, type, file, and message.
    """
    params: dict[str, str] = {
        "componentKeys": project_key,
        "statuses": statuses,
        "ps": str(min(per_page, 500)),
        "p": str(page),
    }
    if severities:
        params["severities"] = severities
    if types:
        params["types"] = types
    if branch:
        params["branch"] = branch

    result = await _get("/issues/search", params)
    if isinstance(result, str):
        return result

    issues = result.get("issues", [])
    total = result.get("total", 0)

    if not issues:
        return f"No issues found for `{project_key}` with the given filters."

    lines = [f"## Issues for {project_key} ({len(issues)} of {total})\n"]
    for issue in issues:
        severity = issue.get("severity", "UNKNOWN")
        emoji = _SEVERITY_EMOJI.get(severity, "⚪")
        issue_type = _TYPE_LABEL.get(issue.get("type", ""), issue.get("type", "—"))
        component = issue.get("component", "—").split(":")[-1]  # Remove project prefix
        line = issue.get("line", "—")
        message = issue.get("message", "—")
        if len(message) > 150:
            message = message[:150] + "…"
        rule = issue.get("rule", "—")

        lines.append(
            f"- {emoji} **{severity}** [{issue_type}] `{component}:{line}`\n"
            f"  {message}\n"
            f"  Rule: `{rule}` | Status: {issue.get('status', '—')}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_issue(issue_key: str) -> str:
    """Get detailed information about a specific SonarQube issue.

    Args:
        issue_key: Issue key (e.g. "AXyz123...").

    Returns:
        Detailed issue information including code context and rule description.
    """
    result = await _get("/issues/search", {"issues": issue_key, "additionalFields": "comments,rules"})
    if isinstance(result, str):
        return result

    issues = result.get("issues", [])
    if not issues:
        return f"Issue {issue_key} not found."

    issue = issues[0]
    severity = issue.get("severity", "UNKNOWN")
    emoji = _SEVERITY_EMOJI.get(severity, "⚪")
    issue_type = _TYPE_LABEL.get(issue.get("type", ""), issue.get("type", "—"))
    component = issue.get("component", "—").split(":")[-1]

    # Get rule details
    rules = result.get("rules", [])
    rule_desc = ""
    if rules:
        rule_desc = f"\n### Rule: {rules[0].get('name', '—')}\n\n{rules[0].get('htmlDesc', '—')[:500]}"

    # Comments
    comments = issue.get("comments", [])
    comments_text = ""
    if comments:
        comments_text = "\n### Comments\n\n"
        for c in comments:
            comments_text += f"- **{c.get('login', '—')}** ({c.get('createdAt', '—')[:16]}): {c.get('markdown', '—')}\n"

    return (
        f"## {emoji} {issue_key}\n\n"
        f"- **Type**: {issue_type}\n"
        f"- **Severity**: {severity}\n"
        f"- **Status**: {issue.get('status', '—')}\n"
        f"- **File**: `{component}` (line {issue.get('line', '—')})\n"
        f"- **Rule**: `{issue.get('rule', '—')}`\n"
        f"- **Message**: {issue.get('message', '—')}\n"
        f"- **Effort**: {issue.get('effort', '—')}\n"
        f"- **Author**: {issue.get('author', '—')}\n"
        f"- **Created**: {issue.get('creationDate', '—')[:16]}\n"
        f"- **Updated**: {issue.get('updateDate', '—')[:16]}\n"
        f"{rule_desc}"
        f"{comments_text}"
    )


# ---------------------------------------------------------------------------
# MCP Tools — Hotspots
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_hotspots(
    project_key: str,
    status: str = "TO_REVIEW",
    branch: str = "",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List security hotspots for a project.

    Args:
        project_key: SonarQube project key.
        status: Filter: "TO_REVIEW", "REVIEWED" (default: "TO_REVIEW").
        branch: Branch name (optional).
        per_page: Results per page (1-500, default: 20).
        page: Page number (default: 1).

    Returns:
        List of security hotspots with vulnerability category and file.
    """
    params: dict[str, str] = {
        "projectKey": project_key,
        "status": status,
        "ps": str(min(per_page, 500)),
        "p": str(page),
    }
    if branch:
        params["branch"] = branch

    result = await _get("/hotspots/search", params)
    if isinstance(result, str):
        return result

    hotspots = result.get("hotspots", [])
    paging = result.get("paging", {})
    total = paging.get("total", 0)

    if not hotspots:
        return f"No security hotspots with status '{status}' found."

    lines = [f"## Security Hotspots ({len(hotspots)} of {total})\n"]
    for h in hotspots:
        category = h.get("securityCategory", "—")
        component = h.get("component", "—").split(":")[-1]
        lines.append(
            f"- **{h.get('message', '—')}**\n"
            f"  Category: {category} | File: `{component}:{h.get('line', '—')}`\n"
            f"  Vulnerability: {h.get('vulnerabilityProbability', '—')}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Code Analysis
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_measures_history(
    project_key: str,
    metrics: str = "bugs,vulnerabilities,code_smells,coverage",
    branch: str = "",
) -> str:
    """Get metrics history for a project (last 10 analyses).

    Args:
        project_key: SonarQube project key.
        metrics: Comma-separated metric keys (default: bugs, vulnerabilities,
            code_smells, coverage).
        branch: Branch name (optional).

    Returns:
        Table showing metric values over recent analyses.
    """
    params: dict[str, str] = {
        "component": project_key,
        "metrics": metrics,
        "ps": "10",
    }
    if branch:
        params["branch"] = branch

    result = await _get("/measures/search_history", params)
    if isinstance(result, str):
        return result

    measures = result.get("measures", [])
    if not measures:
        return f"No metrics history found for `{project_key}`."

    lines = [f"## Metrics History: {project_key}\n"]

    for measure in measures:
        metric = measure.get("metric", "—")
        history = measure.get("history", [])
        lines.append(f"\n### {metric}\n")
        for entry in history[-10:]:  # Last 10 entries
            date = entry.get("date", "—")[:10]
            value = entry.get("value", "—")
            lines.append(f"- {date}: {value}")

    return "\n".join(lines)


@mcp.tool()
async def get_duplications(project_key: str, file_path: str) -> str:
    """Get code duplications for a specific file.

    Args:
        project_key: SonarQube project key.
        file_path: File path within the project (e.g. "src/main/java/App.java").

    Returns:
        List of duplicated blocks with line ranges.
    """
    component_key = f"{project_key}:{file_path}"
    result = await _get("/duplications/show", {"key": component_key})
    if isinstance(result, str):
        return result

    duplications = result.get("duplications", [])
    if not duplications:
        return f"No duplications found in `{file_path}`."

    lines = [f"## Duplications in `{file_path}`\n"]
    for i, dup in enumerate(duplications, 1):
        blocks = dup.get("blocks", [])
        lines.append(f"\n### Duplication #{i} ({len(blocks)} blocks)\n")
        for block in blocks:
            comp = block.get("_ref", "—")
            from_line = block.get("from", "—")
            size = block.get("size", "—")
            lines.append(f"- Lines {from_line}–{int(from_line) + int(size) - 1} (ref: {comp})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Source Code
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_source_with_issues(
    project_key: str,
    file_path: str,
    from_line: int = 1,
    to_line: int = 50,
    branch: str = "",
) -> str:
    """Get source code of a file with inline issue annotations.

    Args:
        project_key: SonarQube project key.
        file_path: File path within the project.
        from_line: Start line (default: 1).
        to_line: End line (default: 50, max range: 500 lines).
        branch: Branch name (optional).

    Returns:
        Source code with issue markers.
    """
    component_key = f"{project_key}:{file_path}"
    params: dict[str, str] = {
        "key": component_key,
        "from": str(from_line),
        "to": str(min(to_line, from_line + 500)),
    }
    if branch:
        params["branch"] = branch

    result = await _get("/sources/lines", params)
    if isinstance(result, str):
        return result

    source_lines = result.get("sources", [])
    if not source_lines:
        return f"No source found for `{file_path}` (lines {from_line}–{to_line})."

    lines = [f"## `{file_path}` (lines {from_line}–{to_line})\n\n```"]
    for sl in source_lines:
        line_num = sl.get("line", "")
        code = sl.get("code", "")
        # Strip HTML tags from SonarQube's highlighted source
        import re
        code_clean = re.sub(r"<[^>]+>", "", code)
        lines.append(f"{line_num:>4} | {code_clean}")
    lines.append("```")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
