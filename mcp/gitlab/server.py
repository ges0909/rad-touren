"""MCP server for GitLab API access.

Provides tools for interacting with a self-hosted GitLab instance
via personal access token authentication.
"""

import os
from urllib.parse import quote_plus, urlencode

import httpx
from fastmcp import FastMCP

mcp = FastMCP("GitLab")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITLAB_URL = os.environ.get("GITLAB_URL", "").rstrip("/")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN", "")


def _headers() -> dict[str, str]:
    return {"PRIVATE-TOKEN": GITLAB_TOKEN, "Content-Type": "application/json"}


def _check_config() -> str | None:
    """Return error message if configuration is missing."""
    if not GITLAB_URL:
        return "Error: GITLAB_URL environment variable is not set."
    if not GITLAB_TOKEN:
        return "Error: GITLAB_TOKEN environment variable is not set."
    return None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def _get(path: str, params: dict | None = None) -> dict | list | str:
    """Send GET request to GitLab API. Returns parsed JSON or error string."""
    err = _check_config()
    if err:
        return err
    url = f"{GITLAB_URL}/api/v4{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.get(url, headers=_headers(), params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"GitLab API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"GitLab connection error: {exc}"


async def _post(path: str, json_body: dict | None = None) -> dict | list | str:
    """Send POST request to GitLab API."""
    err = _check_config()
    if err:
        return err
    url = f"{GITLAB_URL}/api/v4{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.post(url, headers=_headers(), json=json_body)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"GitLab API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"GitLab connection error: {exc}"


async def _put(path: str, json_body: dict | None = None) -> dict | list | str:
    """Send PUT request to GitLab API."""
    err = _check_config()
    if err:
        return err
    url = f"{GITLAB_URL}/api/v4{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.put(url, headers=_headers(), json=json_body)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        return f"GitLab API error (HTTP {exc.response.status_code}): {exc.response.text[:500]}"
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        return f"GitLab connection error: {exc}"


def _encode_project(project_path: str) -> str:
    """URL-encode a project path (namespace/project)."""
    return quote_plus(project_path)


# ---------------------------------------------------------------------------
# MCP Tools — Projects
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_projects(
    search: str = "",
    owned: bool = True,
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List GitLab projects accessible to the authenticated user.

    Args:
        search: Filter projects by name (optional).
        owned: If true, only show projects owned by the user (default: true).
        per_page: Number of results per page (1-100, default: 20).
        page: Page number (default: 1).

    Returns:
        Formatted list of projects with ID, name, path, and URL.
    """
    params: dict[str, str] = {
        "per_page": str(min(per_page, 100)),
        "page": str(page),
        "order_by": "last_activity_at",
        "sort": "desc",
    }
    if search:
        params["search"] = search
    if owned:
        params["owned"] = "true"

    result = await _get("/projects", params)
    if isinstance(result, str):
        return result

    if not result:
        return "No projects found."

    lines = ["## Projects\n"]
    for p in result:
        lines.append(
            f"- **{p['name_with_namespace']}** (ID: {p['id']})\n"
            f"  Path: `{p['path_with_namespace']}`\n"
            f"  URL: {p['web_url']}\n"
            f"  Last activity: {p.get('last_activity_at', 'unknown')}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_project(project: str) -> str:
    """Get details of a specific GitLab project.

    Args:
        project: Project ID (numeric) or path (e.g. "group/project-name").

    Returns:
        Project details including description, default branch, and statistics.
    """
    encoded = _encode_project(project)
    result = await _get(f"/projects/{encoded}", {"statistics": "true"})
    if isinstance(result, str):
        return result

    stats = result.get("statistics", {})
    return (
        f"## {result['name_with_namespace']}\n\n"
        f"- **ID**: {result['id']}\n"
        f"- **Path**: `{result['path_with_namespace']}`\n"
        f"- **URL**: {result['web_url']}\n"
        f"- **Description**: {result.get('description') or '—'}\n"
        f"- **Default branch**: {result.get('default_branch', 'main')}\n"
        f"- **Visibility**: {result.get('visibility', 'unknown')}\n"
        f"- **Created**: {result.get('created_at', 'unknown')}\n"
        f"- **Commits**: {stats.get('commit_count', '?')}\n"
        f"- **Repo size**: {stats.get('repository_size', 0) / 1024 / 1024:.1f} MB\n"
    )


# ---------------------------------------------------------------------------
# MCP Tools — Merge Requests
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_merge_requests(
    project: str,
    state: str = "opened",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List merge requests for a project.

    Args:
        project: Project ID or path (e.g. "group/project-name").
        state: Filter by state: "opened", "closed", "merged", "all" (default: "opened").
        per_page: Number of results per page (1-100, default: 20).
        page: Page number (default: 1).

    Returns:
        Formatted list of merge requests.
    """
    encoded = _encode_project(project)
    params = {"state": state, "per_page": str(per_page), "page": str(page)}
    result = await _get(f"/projects/{encoded}/merge_requests", params)
    if isinstance(result, str):
        return result

    if not result:
        return f"No merge requests with state '{state}' found."

    lines = [f"## Merge Requests ({state})\n"]
    for mr in result:
        labels = ", ".join(mr.get("labels", [])) or "—"
        lines.append(
            f"- **!{mr['iid']}** {mr['title']}\n"
            f"  Author: {mr['author']['name']} | "
            f"Source: `{mr['source_branch']}` → `{mr['target_branch']}`\n"
            f"  Labels: {labels} | Created: {mr['created_at'][:10]}\n"
            f"  URL: {mr['web_url']}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_merge_request(project: str, mr_iid: int) -> str:
    """Get details of a specific merge request.

    Args:
        project: Project ID or path.
        mr_iid: Merge request IID (project-level number).

    Returns:
        Detailed merge request information including description and status.
    """
    encoded = _encode_project(project)
    result = await _get(f"/projects/{encoded}/merge_requests/{mr_iid}")
    if isinstance(result, str):
        return result

    return (
        f"## !{result['iid']} — {result['title']}\n\n"
        f"- **State**: {result['state']}\n"
        f"- **Author**: {result['author']['name']}\n"
        f"- **Source**: `{result['source_branch']}` → `{result['target_branch']}`\n"
        f"- **Created**: {result['created_at']}\n"
        f"- **Updated**: {result['updated_at']}\n"
        f"- **Labels**: {', '.join(result.get('labels', [])) or '—'}\n"
        f"- **Assignees**: {', '.join(a['name'] for a in result.get('assignees', [])) or '—'}\n"
        f"- **Reviewers**: {', '.join(r['name'] for r in result.get('reviewers', [])) or '—'}\n"
        f"- **Merge status**: {result.get('detailed_merge_status', result.get('merge_status', 'unknown'))}\n"
        f"- **Pipeline**: {result.get('pipeline', {}).get('status', 'none') if result.get('pipeline') else 'none'}\n"
        f"- **URL**: {result['web_url']}\n\n"
        f"### Description\n\n{result.get('description') or '—'}\n"
    )


@mcp.tool()
async def get_merge_request_changes(project: str, mr_iid: int) -> str:
    """Get the file changes (diff) of a merge request.

    Args:
        project: Project ID or path.
        mr_iid: Merge request IID.

    Returns:
        List of changed files with diff statistics.
    """
    encoded = _encode_project(project)
    result = await _get(f"/projects/{encoded}/merge_requests/{mr_iid}/changes")
    if isinstance(result, str):
        return result

    changes = result.get("changes", [])
    if not changes:
        return "No file changes in this merge request."

    lines = [f"## Changes in !{mr_iid} ({len(changes)} files)\n"]
    for c in changes:
        status = "new" if c.get("new_file") else "deleted" if c.get("deleted_file") else "modified"
        lines.append(f"- `{c['new_path']}` ({status})")

    return "\n".join(lines)


@mcp.tool()
async def create_merge_request_note(
    project: str, mr_iid: int, body: str
) -> str:
    """Add a comment (note) to a merge request.

    Args:
        project: Project ID or path.
        mr_iid: Merge request IID.
        body: Comment text (supports Markdown).

    Returns:
        Confirmation with the created note ID.
    """
    encoded = _encode_project(project)
    result = await _post(
        f"/projects/{encoded}/merge_requests/{mr_iid}/notes",
        {"body": body},
    )
    if isinstance(result, str):
        return result

    return f"Comment added (note ID: {result['id']}) to !{mr_iid}."


# ---------------------------------------------------------------------------
# MCP Tools — Pipelines
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_pipelines(
    project: str,
    status: str = "",
    ref: str = "",
    per_page: int = 10,
) -> str:
    """List recent pipelines for a project.

    Args:
        project: Project ID or path.
        status: Filter by status: "running", "pending", "success", "failed",
            "canceled", "skipped" (optional, shows all if empty).
        ref: Filter by branch/tag name (optional).
        per_page: Number of results (1-100, default: 10).

    Returns:
        Formatted list of pipelines with status and duration.
    """
    encoded = _encode_project(project)
    params: dict[str, str] = {"per_page": str(per_page), "order_by": "id", "sort": "desc"}
    if status:
        params["status"] = status
    if ref:
        params["ref"] = ref

    result = await _get(f"/projects/{encoded}/pipelines", params)
    if isinstance(result, str):
        return result

    if not result:
        return "No pipelines found."

    lines = ["## Pipelines\n"]
    for p in result:
        duration = f"{p['duration']}s" if p.get("duration") else "—"
        lines.append(
            f"- **#{p['id']}** [{p['status']}] on `{p['ref']}`\n"
            f"  Duration: {duration} | Created: {p['created_at'][:16]}\n"
            f"  URL: {p['web_url']}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_pipeline_jobs(project: str, pipeline_id: int) -> str:
    """Get jobs of a specific pipeline.

    Args:
        project: Project ID or path.
        pipeline_id: Pipeline ID.

    Returns:
        List of jobs with their status, stage, and duration.
    """
    encoded = _encode_project(project)
    result = await _get(f"/projects/{encoded}/pipelines/{pipeline_id}/jobs")
    if isinstance(result, str):
        return result

    if not result:
        return "No jobs found for this pipeline."

    lines = [f"## Pipeline #{pipeline_id} Jobs\n"]
    for j in result:
        duration = f"{j.get('duration', 0):.0f}s" if j.get("duration") else "—"
        lines.append(
            f"- **{j['name']}** [{j['status']}] (Stage: {j['stage']})\n"
            f"  Duration: {duration} | Runner: {j.get('runner', {}).get('description', '—')}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Issues
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_issues(
    project: str,
    state: str = "opened",
    labels: str = "",
    search: str = "",
    per_page: int = 20,
    page: int = 1,
) -> str:
    """List issues for a project.

    Args:
        project: Project ID or path.
        state: Filter by state: "opened", "closed", "all" (default: "opened").
        labels: Comma-separated label names to filter by (optional).
        search: Search in title and description (optional).
        per_page: Number of results per page (1-100, default: 20).
        page: Page number (default: 1).

    Returns:
        Formatted list of issues.
    """
    encoded = _encode_project(project)
    params: dict[str, str] = {
        "state": state,
        "per_page": str(per_page),
        "page": str(page),
    }
    if labels:
        params["labels"] = labels
    if search:
        params["search"] = search

    result = await _get(f"/projects/{encoded}/issues", params)
    if isinstance(result, str):
        return result

    if not result:
        return f"No issues with state '{state}' found."

    lines = [f"## Issues ({state})\n"]
    for issue in result:
        assignee = issue.get("assignee", {})
        assignee_name = assignee.get("name", "unassigned") if assignee else "unassigned"
        issue_labels = ", ".join(issue.get("labels", [])) or "—"
        lines.append(
            f"- **#{issue['iid']}** {issue['title']}\n"
            f"  Assignee: {assignee_name} | Labels: {issue_labels}\n"
            f"  Created: {issue['created_at'][:10]} | URL: {issue['web_url']}\n"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Repository / Files
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_file(project: str, file_path: str, ref: str = "") -> str:
    """Get the content of a file from the repository.

    Args:
        project: Project ID or path.
        file_path: Path to the file in the repository (e.g. "src/main.py").
        ref: Branch, tag, or commit SHA (default: project's default branch).

    Returns:
        File content as text.
    """
    encoded = _encode_project(project)
    encoded_path = quote_plus(file_path)
    params: dict[str, str] = {}
    if ref:
        params["ref"] = ref

    result = await _get(f"/projects/{encoded}/repository/files/{encoded_path}", params)
    if isinstance(result, str):
        return result

    import base64
    content = base64.b64decode(result.get("content", "")).decode("utf-8", errors="replace")
    return (
        f"## {file_path} (ref: {result.get('ref', 'default')})\n\n"
        f"```\n{content}\n```"
    )


@mcp.tool()
async def list_repository_tree(
    project: str,
    path: str = "",
    ref: str = "",
    recursive: bool = False,
    per_page: int = 50,
) -> str:
    """List files and directories in a repository.

    Args:
        project: Project ID or path.
        path: Directory path within the repository (default: root).
        ref: Branch, tag, or commit SHA (optional).
        recursive: List files recursively (default: false).
        per_page: Number of results (1-100, default: 50).

    Returns:
        Tree listing of files and directories.
    """
    encoded = _encode_project(project)
    params: dict[str, str] = {"per_page": str(per_page)}
    if path:
        params["path"] = path
    if ref:
        params["ref"] = ref
    if recursive:
        params["recursive"] = "true"

    result = await _get(f"/projects/{encoded}/repository/tree", params)
    if isinstance(result, str):
        return result

    if not result:
        return "No files found at this path."

    lines = [f"## Repository tree: /{path}\n"]
    for item in result:
        icon = "📁" if item["type"] == "tree" else "📄"
        lines.append(f"- {icon} `{item['path']}`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools — Search
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_code(
    project: str,
    query: str,
    ref: str = "",
) -> str:
    """Search for code within a project.

    Args:
        project: Project ID or path.
        query: Search query string.
        ref: Branch or tag to search in (optional).

    Returns:
        List of matching files with line excerpts.
    """
    encoded = _encode_project(project)
    params: dict[str, str] = {"scope": "blobs", "search": query}
    if ref:
        params["ref"] = ref

    result = await _get(f"/projects/{encoded}/search", params)
    if isinstance(result, str):
        return result

    if not result:
        return f'No code matches found for "{query}".'

    lines = [f'## Code search: "{query}"\n']
    for item in result[:20]:  # Limit output
        lines.append(
            f"- `{item['filename']}` (ref: {item.get('ref', '—')})\n"
            f"  ```\n  {item.get('data', '')[:200]}\n  ```\n"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
