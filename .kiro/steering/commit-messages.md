---
inclusion: always
---

# Commit Messages

All git commits in this project use [Conventional Commits](https://www.conventionalcommits.org/) format. Language is always **English**, regardless of the conversation language.

## Format

```
<type>: <short summary>

<optional body>
```

## Subject Line Rules

- Imperative mood ("add feature", not "added feature")
- All lowercase, no trailing period
- Maximum 70 characters
- Must start with one of the allowed types

## Allowed Types

| Type       | Use for                                     |
| ---------- | ------------------------------------------- |
| `feat`     | New functionality, new tours, new MCP tools |
| `fix`      | Bug fixes, corrected data, broken routes    |
| `docs`     | Documentation, READMEs, tour descriptions   |
| `refactor` | Code restructuring without behavior change  |
| `chore`    | Dependency updates, config changes, cleanup |
| `style`    | Formatting, whitespace, linting (no logic)  |
| `test`     | Adding or updating tests                    |
| `ci`       | CI/CD pipeline changes                      |

## Scope

Do **not** use parenthesized scopes. Keep it flat: `type: summary`.

## Body

- Optional but encouraged for multi-file changes
- Bullet list, each line starting with `-`
- Keep lines under 80 characters
- Reference tour names, file names, or MCP server names when relevant

## Examples

```
feat: add elevation profile rendering to brouter MCP

- implement render_elevation_profile tool
- add matplotlib dependency
- include property-based tests for chart output
```

```
docs: update sardinia roadtrip with restaurant picks
```

## Auto-Commit Behavior

When the user types **"commit"** (or equivalent like "committen", "einchecken"):

1. Generate a commit message following the rules above based on the current `git diff --staged` or working tree changes
2. Run `git add -A`
3. Run `git commit -m "<generated message>"` (with body via `-m` flag if needed)
4. Do **not** ask for confirmation — execute immediately
5. Do **not** push unless explicitly asked
