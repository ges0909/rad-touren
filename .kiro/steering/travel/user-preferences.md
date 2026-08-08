---
inclusion: fileMatch
fileMatchPattern: "trips/**"
---

# Universal Travel Preferences — Gerrit on Tour

These rules apply to all travel types (cycling, hiking, roadtrips). Type-specific preferences are in separate steering files (`bike-preferences.md`, `road-preferences.md`).

## User Profile

- **Home base:** S Blankenfelde (TF) Bhf, Berlin
- **Default group size:** 2 persons
- **Travel types:** Cycling day trips, multi-day roadtrips

## Language Rules

- Write tour content in the language matching the user's prompt language.
- Code artifacts are always English kebab-case: file names, GPX metadata, MCP tool parameters, commit messages.

## Interest Categories

Use these categories and emojis consistently across all tour documents. When a location matches multiple categories, list them in priority order defined by the active type-specific preferences file.

| Emoji | Category           | Scope                                                 |
| ----- | ------------------ | ----------------------------------------------------- |
| 🥾    | Wandern            | Hiking trails, nature paths, viewpoints               |
| 🏊    | Baden              | Lakes, beaches, thermal baths, natural swimming spots |
| 🍷    | Regionale Küche    | Local restaurants, markets, food specialties          |
| 🌿    | Botanische Gärten  | Botanical gardens, arboreta, landscape parks          |
| 🎨    | Moderne Kunst      | Galleries, sculpture parks, contemporary art museums  |
| 🏛️    | Sehenswürdigkeiten | Historic sites, monuments, museums                    |

Additional contextual emoji: `🍺` for beer gardens/restaurants (maps to Overpass `einkehr` preset).

## Content Integrity (Non-Negotiable)

These rules override all other considerations when generating tour content:

1. **No fabrication.** Only present data sourced from API results or web search. If data is unavailable, state it explicitly — never invent details.
2. **Deduplication.** One entry per POI. Remove duplicates within a 200 m radius.
3. **Seasonal awareness.** Flag closures, limited opening hours, and off-season risks.
4. **Source attribution.** Append `ℹ️ Zuletzt geprüft: {YYYY-MM-DD}` to web-sourced data.
5. **Link policy.** Only official websites for major POIs. Never use Google Maps, TripAdvisor, or ephemeral URLs.
6. **Link verification.** Before inserting any URL, confirm HTTP 200 via `web_fetch`. Remove or replace dead links.
7. **Unverifiable data.** Mark with `ℹ️ Nicht verifiziert.` — never guess or fabricate.

## Route Discovery Workflow

### Waymarked Trails (Marked Routes)

Use these MCP tools in sequence for route research:

1. `search_routes(query, activity)` — find routes by name, region, or keyword
2. `get_route_details(route_id, activity)` — retrieve distance, markings, operator
3. `get_route_segments(route_id, activity)` — get stages and waypoints along the route

### Review Lookup (Hiking Routes)

Always look up reviews when recommending hiking routes. Apply these thresholds:

- **Prefer:** ≥ 4.0 stars with ≥ 30 reviews
- **Discard:** < 3.5 stars or < 10 reviews (unless no alternative exists)

Search procedure:

1. `"{route name}" AllTrails review`
2. `"{route name}" Komoot Bewertung`
3. `"{route name}" Wikiloc rating` (especially for Spain/Portugal)
4. Summarize: rating, praise/criticism, difficulty, trail surface
5. Append: `ℹ️ Bewertungen aus Web-Recherche ({YYYY-MM-DD}), nicht per API verifiziert.`

### Tool Selection

| Intent                     | Tool                                            |
| -------------------------- | ----------------------------------------------- |
| Find routes in a region    | `search_routes` (Waymarked Trails)              |
| Route recommendation       | `search_routes` + `get_route_details`           |
| Route ratings/reviews      | Web search (AllTrails / Komoot)                 |
| Custom cycling route       | BRouter `calculate_route`                       |
| Custom car or hiking route | OpenRouteService `calculate_route`              |
| Experience reports         | Web search (Komoot / AllTrails / Outdooractive) |

## Output Structure

Every tour request produces at minimum:

- Markdown document: `trips/{type}/{tour-name}/index.md`
- GPX track(s): `trips/{type}/{tour-name}/gpx/{segment-name}.gpx`
- Route map PNG: `trips/{type}/{tour-name}/maps/route-map.png`

Additional outputs are defined in the type-specific output template (`bike-output-template.md`, `road-output-template.md`).
