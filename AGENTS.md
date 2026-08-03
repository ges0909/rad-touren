# Gerrit on Tour — AI Context

Universal guidelines for all AI assistants in this repository.

## Repository Overview

**Gerrit on Tour** is an AI-powered travel planning tool serving two purposes:

1. **Personal Travel Planning** — Planning and documenting bike, car, and hiking tours
2. **Platform Development** — Developing the web app, MCP servers, and infrastructure

**Important:** This repository separates both contexts consistently:

- When working in `trips/**` → Travel planning context active (user perspective)
- When working in `app/**`, `mcp/**` → Development context active (developer perspective)

Context-specific rules are organized in `.kiro/steering/` with fileMatch patterns and are loaded automatically based on active files.

---

# Commit Messages

All git commits in this project use [Conventional Commits](https://www.conventionalcommits.org/) format. Language is always **English**, regardless of the conversation language.

## Format

```
<type>(<optional-scope>): <short summary>

<optional body>
```

## Subject Line Rules

- Imperative mood ("add feature", not "added feature")
- All lowercase, no trailing period
- Maximum 70 characters
- Must start with one of the allowed types
- Scope is optional but recommended for larger changes

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

## Scopes

Optional, use when helpful for clarity. Common scopes:

| Scope      | Use for                          |
| ---------- | -------------------------------- |
| `mcp`      | MCP server changes (any server)  |
| `frontend` | Vue 3 frontend changes           |
| `backend`  | FastAPI backend changes          |
| `trip`     | Tour/trip content updates        |
| `docs`     | Documentation (concepts, guides) |
| `ci`       | CI/CD configuration              |

Examples: `feat(mcp): add elevation profile tool`, `docs(trip): update sardinia itinerary`

## Body

- Optional but encouraged for multi-file changes
- Bullet list, each line starting with `-`
- Keep lines under 80 characters
- Reference tour names, file names, or MCP server names when relevant

## Examples

```
feat(mcp): add elevation profile rendering to brouter

- implement render_elevation_profile tool
- add matplotlib dependency
- include property-based tests for chart output
```

```
docs(trip): update sardinia roadtrip with restaurant picks
```

```
fix: correct GPX coordinate ordering in bike routes
```

## Auto-Commit Behavior

When the user types **"commit"** (or equivalent like "committen", "einchecken"):

1. Generate a commit message following the rules above based on `git diff --staged` or working tree changes
2. Run `git add -A`
3. Run `git commit -m "<generated message>"` (with body via `-m` flag if needed)
4. Do **not** ask for confirmation — execute immediately
5. Do **not** push unless explicitly asked

---

## Context-Specific Rules

The following additional rules are loaded automatically based on active files:

### Reiseplanung (active in `trips/**`)

- `user-preferences.md` — Universal travel preferences, home base, content integrity
- `bike-preferences.md` — Cycling tour preferences (distance, terrain, interests, food)
- `bike-planner.md` — Cycling tour workflow + BRouter/VBB rules
- `bike-output-template.md` — Cycling tour output format
- `road-preferences.md` — Roadtrip preferences (flights, accommodation, food, interests)
- `road-planner.md` — Roadtrip workflow + ORS/OSRM rules
- `road-output-template.md` — Roadtrip output format

### App-Entwicklung (active in `app/**`, `mcp/**`, `docs/**`, `scripts/**`)

- `app-product.md` — Platform architecture, tech stack, MCP ecosystem, naming conventions
- `mcp-development.md` — MCP server development guidelines
- `app/AGENTS.md` — Web app coding guidelines (Vue 3 + FastAPI)

**Note:** You do not need to manually load these files. Kiro's fileMatch system loads them automatically when you work on matching files.
