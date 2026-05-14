# Jira Cloud MCP Server

MCP server for accessing Jira Cloud via Personal Access Token (PAT).

## Setup

1. Create a Personal Access Token in Jira Cloud:
   - Profile → Security → Create and manage API tokens
   - Or: https://id.atlassian.com/manage-profile/security/api-tokens

2. Configure environment variables in `.env`:

   ```
   JIRA_URL=https://your-org.atlassian.net
   JIRA_TOKEN=your-personal-access-token
   JIRA_EMAIL=your-email@company.com
   ```

3. Install dependencies:

   ```bash
   cd mcp/jira
   uv sync
   ```

4. Enable in `.kiro/settings/mcp.json` by setting `"disabled": false`

## Tools

| Tool                 | Description                                            |
| -------------------- | ------------------------------------------------------ |
| `search_issues`      | Search issues via JQL                                  |
| `get_issue`          | Get detailed issue info (description, subtasks, links) |
| `get_issue_comments` | Get comments on an issue                               |
| `add_comment`        | Add a comment to an issue                              |
| `transition_issue`   | Move issue to a new status                             |
| `assign_issue`       | Assign/unassign an issue                               |
| `list_boards`        | List Scrum/Kanban boards                               |
| `get_sprint_issues`  | Get issues in active/future sprint                     |
| `search_users`       | Search users by name/email                             |

## Authentication

Uses Bearer token authentication (`Authorization: Bearer <PAT>`).
For Jira Cloud with API tokens (email + token as basic auth), adjust
the `_headers()` function if needed.

## JQL Examples

```
project = MYPROJ AND status = "In Progress"
assignee = currentUser() AND sprint in openSprints()
labels = "backend" AND created >= -7d
priority in (Blocker, Critical) AND status != Done
```
