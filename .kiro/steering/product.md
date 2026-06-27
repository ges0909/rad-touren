# Product

**Gerrit on Tour** — AI-powered personal tour planner for cycling day trips, multi-day road trips, and hiking (planned). Home base: S Blankenfelde (TF) Bhf, Berlin. Travel group: 2 persons.

## Two Usage Modes

1. **Kiro (primary)** — open the project in Kiro, type a tour request in chat. MCP servers supply routing, weather, POIs, transit, and travel content. Steering files guide the planning workflow. Results are saved as Markdown + GPX under `trips/`.

2. **Web app** — standalone browser UI (Vue 3 + FastAPI) replicating the same Gemini agent loop, accessible without Kiro.

## Tour Types

| Type         | Area                                             | Status  |
| ------------ | ------------------------------------------------ | ------- |
| 🚴 Cycling   | Berlin/Brandenburg day trips via regional trains | Active  |
| 🥾 Hiking    | Berlin/Brandenburg day hikes                     | Planned |
| 🚗 Roadtrips | Multi-day car trips across Europe                | Active  |

## Output

A single prompt produces a complete tour: Markdown trip doc, GPX track, rendered route map (PNG), elevation profile (PNG), POIs, weather forecast, transit connections, and event/accommodation info — all written to `trips/{type}/{tour-name}/`.
