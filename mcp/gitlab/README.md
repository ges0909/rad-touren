# GitLab MCP Server

MCP server for accessing a self-hosted GitLab instance via Personal Access Token.

## Setup

1. Create a Personal Access Token in GitLab:
   - Settings → Access Tokens
   - Scopes: `api`, `read_repository`

2. Configure environment variables in `.env`:

   ```
   GITLAB_URL=https://gitlab.your-company.com
   GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
   ```

3. Install dependencies:

   ```bash
   cd mcp/gitlab
   uv sync
   ```

4. Enable in `.kiro/settings/mcp.json` by setting `"disabled": false`

## Tools

| Tool                        | Description                                       |
| --------------------------- | ------------------------------------------------- |
| `list_projects`             | List accessible projects (search, filter owned)   |
| `get_project`               | Get project details with statistics               |
| `list_merge_requests`       | List MRs by state (opened/merged/closed)          |
| `get_merge_request`         | Get MR details (description, pipeline, reviewers) |
| `get_merge_request_changes` | Get file diffs of a MR                            |
| `create_merge_request_note` | Add a comment to a MR                             |
| `list_pipelines`            | List recent pipelines with status                 |
| `get_pipeline_jobs`         | Get jobs of a specific pipeline                   |
| `list_issues`               | List project issues with filters                  |
| `get_file`                  | Read a file from the repository                   |
| `list_repository_tree`      | Browse repository file tree                       |
| `search_code`               | Search for code within a project                  |

## Authentication

Uses the `PRIVATE-TOKEN` header with a Personal Access Token.
SSL verification is disabled (`verify=False`) for self-signed certificates
common in intranet deployments.
