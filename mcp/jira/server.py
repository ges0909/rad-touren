"""MCP server for Jira Cloud API access.

Provides tools for interacting with Jira Cloud
via personal access token (PAT) authentication.
"""

import os
from urllib.parse import urlencode

import httpx
from fastmcp import FastMCP

mcp = FastMCP("Jira Cloud")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JIRA_URL = os.environ.get("JIRA_URL", "").rstrip("/")
JIRA_TOKEN = os.environ.get("JIRA_TOKEN", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _check_config() -> str | None:
    """Return error message if configuration is missing."""
    if not JIRA_URL:
        return "Error: JIRA_URL environment variable is not set."
    if not JIRA_TOKEN:
        return "Error: JIRA_TOKEN environment variable is not set."
    return None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def _get(path: str, params: dict | None = None) -> dict | list | str:
    """Send GET request to Jira REST API. Returns parsed JSON or error string."""
    err = _check_config()
    if err:
        return err
    url = f"{JIRA_URL}/rest/api/3{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=_headers(), params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"Jira API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"


async def _post(path: str, json_body: dict | None = None) -> dict | list | str:
    """Send POST request to Jira REST API."""
    err = _check_config()
    if err:
        return err
    url = f"{JIRA_URL}/rest/api/3{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=_headers(), json=json_body)
            resp.raise_for_status()
            if resp.status_code == 204:
                return {}
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"Jira API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"


async def _put(path: str, json_body: dict | None = None) -> dict | str:
    """Send PUT request to Jira REST API."""
    err = _check_config()
    if err:
        return err
    url = f"{JIRA_URL}/rest/api/3{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(url, headers=_headers(), json=json_body)
            resp.raise_for_status()
            if resp.status_code == 204:
                return {}
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"Jira API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_adf_to_text(adf: dict | None) -> str:
    """Convert Atlassian Document Format (ADF) to plain text (simplified)."""
    if not adf:
        return "—"
    text_parts: list[str] = []

    def _extract(node: dict) -> None:
        if node.get("type") == "text":
            text_parts.append(node.get("text", ""))
        for child in node.get("content", []):
            _extract(child)

    _extract(adf)
    return "".join(text_parts) or "—"


# ---------------------------------------------------------------------------
# MCP Tools — Search / JQL
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_issues(
    jql: str,
    max_results: int = 20,
    fields: str = "summary,status,assignee,priority,labels,created,updated",
) -> str:
    """Search for Jira issues using JQL (Jira Query Language).

    Args:
        jql: JQL query string (e.g. "project = MYPROJ AND status = 'In Progress'").
        max_results: Maximum number of results (1-50, default: 20).
        fields: Comma-separated list of fields to return (default: common fields).

    Returns:
        Formatted list of matching issues.
    """
    params = {
        "jql": jql,
        "maxResults": str(min(max_results, 50)),
        "fields": fields,
    }
    result = await _get("/search", params)
    if isinstance(result, str):
        return result

    issues = result.get("issues", [])
    total = result.get("total", 0)

    if not issues:
        return f"No issues found for JQL: `{jql}`"

    lines = [f"## Jira Issues ({len(issues)} of {total} results)\n"]
    for issue in issues:
        f = issue.get("fields", {})
        status = f.get("status", {}).get("name", "—")
        assignee = f.get("assignee", {})
        assignee_name = assignee.get("displayName", "unassigned") if assignee else "unassigned"
        priority = f.get("priority", {}).get("name", "—") if f.get("priority") else "—"
        labels = ", ".join(f.get("labels", [])) or "—"
        lines.append(
            f"- **{issue['key']}** {f.get('summary', '—')}\n"
            f"  Status: {status} | Assignee: {assignee_name} | Priority: {priority}\n"
            f"  Labels: {labels} | Updated: {f.get('updated', '—')[:10]}\n"
            f"  URL: {JIRA_URL}/browse/{issue['key']}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Issue Details
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_issue(issue_key: str) -> str:
    """Get detailed information about a specific Jira issue.

    Args:
        issue_key: Issue key (e.g. "PROJ-123").

    Returns:
        Detailed issue information including description, comments count, and links.
    """
    result = await _get(f"/issue/{issue_key}")
    if isinstance(result, str):
        return result

    f = result.get("fields", {})
    status = f.get("status", {}).get("name", "—")
    issue_type = f.get("issuetype", {}).get("name", "—")
    priority = f.get("priority", {}).get("name", "—") if f.get("priority") else "—"
    assignee = f.get("assignee", {})
    assignee_name = assignee.get("displayName", "unassigned") if assignee else "unassigned"
    reporter = f.get("reporter", {})
    reporter_name = reporter.get("displayName", "—") if reporter else "—"
    labels = ", ".join(f.get("labels", [])) or "—"
    components = ", ".join(c.get("name", "") for c in f.get("components", [])) or "—"
    fix_versions = ", ".join(v.get("name", "") for v in f.get("fixVersions", [])) or "—"
    sprint_field = f.get("sprint")
    sprint_name = sprint_field.get("name", "—") if isinstance(sprint_field, dict) else "—"

    description = _format_adf_to_text(f.get("description"))
    # Truncate long descriptions
    if len(description) > 1000:
        description = description[:1000] + "…"

    parent = f.get("parent", {})
    parent_info = f"{parent['key']} — {parent.get('fields', {}).get('summary', '')}" if parent else "—"

    subtasks = f.get("subtasks", [])
    subtask_lines = ""
    if subtasks:
        subtask_lines = "\n### Subtasks\n\n"
        for st in subtasks:
            st_status = st.get("fields", {}).get("status", {}).get("name", "—")
            subtask_lines += f"- **{st['key']}** {st.get('fields', {}).get('summary', '—')} [{st_status}]\n"

    return (
        f"## {result['key']} — {f.get('summary', '—')}\n\n"
        f"- **Type**: {issue_type}\n"
        f"- **Status**: {status}\n"
        f"- **Priority**: {priority}\n"
        f"- **Assignee**: {assignee_name}\n"
        f"- **Reporter**: {reporter_name}\n"
        f"- **Labels**: {labels}\n"
        f"- **Components**: {components}\n"
        f"- **Fix versions**: {fix_versions}\n"
        f"- **Sprint**: {sprint_name}\n"
        f"- **Parent**: {parent_info}\n"
        f"- **Created**: {f.get('created', '—')[:16]}\n"
        f"- **Updated**: {f.get('updated', '—')[:16]}\n"
        f"- **URL**: {JIRA_URL}/browse/{result['key']}\n\n"
        f"### Description\n\n{description}\n"
        f"{subtask_lines}"
    )


@mcp.tool()
async def get_issue_comments(issue_key: str, max_results: int = 10) -> str:
    """Get comments on a Jira issue.

    Args:
        issue_key: Issue key (e.g. "PROJ-123").
        max_results: Maximum number of comments to return (default: 10).

    Returns:
        List of comments with author and timestamp.
    """
    params = {"maxResults": str(max_results), "orderBy": "-created"}
    result = await _get(f"/issue/{issue_key}/comment", params)
    if isinstance(result, str):
        return result

    comments = result.get("comments", [])
    if not comments:
        return f"No comments on {issue_key}."

    lines = [f"## Comments on {issue_key} ({len(comments)} shown)\n"]
    for c in comments:
        author = c.get("author", {}).get("displayName", "Unknown")
        created = c.get("created", "—")[:16]
        body = _format_adf_to_text(c.get("body"))
        if len(body) > 500:
            body = body[:500] + "…"
        lines.append(f"### {author} ({created})\n\n{body}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Issue Actions
# ---------------------------------------------------------------------------


@mcp.tool()
async def add_comment(issue_key: str, body: str) -> str:
    """Add a comment to a Jira issue.

    Args:
        issue_key: Issue key (e.g. "PROJ-123").
        body: Comment text (plain text, will be converted to ADF).

    Returns:
        Confirmation message.
    """
    # Convert plain text to minimal ADF
    adf_body = {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": body}],
            }
        ],
    }
    result = await _post(f"/issue/{issue_key}/comment", {"body": adf_body})
    if isinstance(result, str):
        return result

    return f"Comment added to {issue_key} (ID: {result.get('id', '—')})."


@mcp.tool()
async def transition_issue(issue_key: str, transition_name: str) -> str:
    """Transition a Jira issue to a new status.

    First retrieves available transitions, then executes the matching one.

    Args:
        issue_key: Issue key (e.g. "PROJ-123").
        transition_name: Target status name (e.g. "In Progress", "Done").
            Case-insensitive partial match is supported.

    Returns:
        Confirmation or list of available transitions if no match found.
    """
    # Get available transitions
    result = await _get(f"/issue/{issue_key}/transitions")
    if isinstance(result, str):
        return result

    transitions = result.get("transitions", [])
    if not transitions:
        return f"No transitions available for {issue_key}."

    # Find matching transition (case-insensitive partial match)
    target = transition_name.lower()
    match = None
    for t in transitions:
        if target in t["name"].lower() or target in t.get("to", {}).get("name", "").lower():
            match = t
            break

    if not match:
        available = ", ".join(f"'{t['name']}'" for t in transitions)
        return (
            f"No transition matching '{transition_name}' found for {issue_key}.\n"
            f"Available transitions: {available}"
        )

    # Execute transition
    err = _check_config()
    if err:
        return err
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                headers=_headers(),
                json={"transition": {"id": match["id"]}},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return f"Transition failed (HTTP {exc.response.status_code}): {exc.response.text[:300]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"

    return f"{issue_key} transitioned to '{match['to']['name']}'."


@mcp.tool()
async def assign_issue(issue_key: str, account_id: str = "") -> str:
    """Assign a Jira issue to a user.

    Args:
        issue_key: Issue key (e.g. "PROJ-123").
        account_id: Atlassian account ID of the assignee.
            Leave empty to unassign.

    Returns:
        Confirmation message.
    """
    body = {"accountId": account_id if account_id else None}
    result = await _put(f"/issue/{issue_key}/assignee", body)
    if isinstance(result, str):
        return result

    if account_id:
        return f"{issue_key} assigned to account {account_id}."
    return f"{issue_key} unassigned."


# ---------------------------------------------------------------------------
# MCP Tools — Boards & Sprints
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_boards(project_key: str = "", board_type: str = "") -> str:
    """List Jira boards (Scrum/Kanban).

    Args:
        project_key: Filter by project key (optional).
        board_type: Filter by type: "scrum", "kanban" (optional).

    Returns:
        List of boards with ID, name, and type.
    """
    err = _check_config()
    if err:
        return err

    params: dict[str, str] = {}
    if project_key:
        params["projectKeyOrId"] = project_key
    if board_type:
        params["type"] = board_type

    url = f"{JIRA_URL}/rest/agile/1.0/board"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=_headers(), params=params)
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPStatusError as exc:
        return f"Jira API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"

    boards = result.get("values", [])
    if not boards:
        return "No boards found."

    lines = ["## Boards\n"]
    for b in boards:
        lines.append(f"- **{b['name']}** (ID: {b['id']}, Type: {b.get('type', '—')})")

    return "\n".join(lines)


@mcp.tool()
async def get_sprint_issues(
    board_id: int,
    sprint_state: str = "active",
) -> str:
    """Get issues in the current/active sprint of a board.

    Args:
        board_id: Board ID (from list_boards).
        sprint_state: Sprint state filter: "active", "future", "closed" (default: "active").

    Returns:
        List of issues in the sprint grouped by status.
    """
    err = _check_config()
    if err:
        return err

    # Get sprints for the board
    url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url, headers=_headers(), params={"state": sprint_state}
            )
            resp.raise_for_status()
            sprints_result = resp.json()
    except httpx.HTTPStatusError as exc:
        return f"Jira API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"

    sprints = sprints_result.get("values", [])
    if not sprints:
        return f"No {sprint_state} sprints found for board {board_id}."

    # Use the first (most recent) sprint
    sprint = sprints[0]

    # Get issues in that sprint
    sprint_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint['id']}/issue"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                sprint_url,
                headers=_headers(),
                params={"maxResults": "50", "fields": "summary,status,assignee,priority"},
            )
            resp.raise_for_status()
            issues_result = resp.json()
    except httpx.HTTPStatusError as exc:
        return f"Jira API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"Jira connection error: {exc}"

    issues = issues_result.get("issues", [])
    if not issues:
        return f"No issues in sprint '{sprint['name']}'."

    # Group by status
    by_status: dict[str, list[str]] = {}
    for issue in issues:
        f = issue.get("fields", {})
        status = f.get("status", {}).get("name", "Unknown")
        assignee = f.get("assignee", {})
        assignee_name = assignee.get("displayName", "—") if assignee else "—"
        entry = f"  - **{issue['key']}** {f.get('summary', '—')} ({assignee_name})"
        by_status.setdefault(status, []).append(entry)

    lines = [f"## Sprint: {sprint['name']}\n"]
    lines.append(f"Goal: {sprint.get('goal', '—')}\n")
    lines.append(f"Start: {sprint.get('startDate', '—')[:10]} | End: {sprint.get('endDate', '—')[:10]}\n")

    for status, entries in by_status.items():
        lines.append(f"\n### {status} ({len(entries)})\n")
        lines.extend(entries)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — User Search
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_users(query: str, max_results: int = 10) -> str:
    """Search for Jira users by name or email.

    Args:
        query: Search string (name, email, or username).
        max_results: Maximum results (1-50, default: 10).

    Returns:
        List of matching users with account IDs.
    """
    params = {"query": query, "maxResults": str(max_results)}
    result = await _get("/user/search", params)
    if isinstance(result, str):
        return result

    if not result:
        return f'No users found for "{query}".'

    lines = [f'## Users matching "{query}"\n']
    for u in result:
        lines.append(
            f"- **{u.get('displayName', '—')}**\n"
            f"  Account ID: `{u.get('accountId', '—')}`\n"
            f"  Email: {u.get('emailAddress', '—')}\n"
            f"  Active: {u.get('active', '—')}\n"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
