---
inclusion: automatic
---

# Radtouren-Planung — Berlin/Brandenburg

Guide for planning, generating, and presenting cycling tours in the Berlin/Brandenburg region.

## Language

- All tour output (descriptions, highlights, summaries, markdown files) MUST be in **German**.
- Tool calls, code identifiers, and file names use English/kebab-case.

## Coordinate Convention

- Format: `[longitude, latitude]` — longitude first. Applies to all MCP tool calls.
- Scope: Berlin/Brandenburg. Tours start from locations reachable by public transit from Blankenfelde-Mahlow.
- Geocoding: Use `mcp_brouter_search_location` (Nominatim). Verify coordinates fall within Berlin/Brandenburg (lat ~51.3–53.6, lon ~11.3–14.8).

## Routing

- Use `mcp_brouter_calculate_route` with `profile=trekking` (default).
- The `trekking` profile automatically prefers designated cycle paths (`highway=cycleway`), regional/national cycling routes, and quiet side roads. No manual avoidance rules needed.
- Use **3–6 intermediate waypoints** to define the route shape for round trips.
- BRouter handles waypoint snapping gracefully — no 404 errors like OpenRouteService.

### Round Trips (Rundtouren)

- First and last waypoint must be identical (same coordinates).
- Define route shape through intermediate waypoints.
- Choose start/end points with good public transit access (S-Bahn, Regionalbahn).
- Avoid unnecessary detours — verify waypoints form a logical loop without backtracking.

## Well-Known Regional Cycling Routes

Reference these when selecting waypoints and describing segments:

| Route             | Description                                            |
| ----------------- | ------------------------------------------------------ |
| Havelradweg       | Along the Havel from Potsdam via Werder to Brandenburg |
| Europaradweg R1   | Passes through Potsdam and Werder                      |
| Berliner Mauerweg | Loop along the former Berlin Wall                      |
| Spreeradweg       | Along the Spree through Berlin and surroundings        |
| Dahme-Radweg      | Along the Dahme south of Berlin                        |
| Oder-Havel-Radweg | North of Berlin                                        |
| Tour Brandenburg  | Long-distance loop around Brandenburg                  |
| Gurkenradweg      | Through the Spreewald                                  |

## MCP Tool Usage

### Route Calculation — `mcp_brouter_calculate_route`

- Required: `waypoints` (list of `[lon, lat]` pairs, minimum 2).
- Optional: `profile` (default `trekking`), `format` (`gpx`/`geojson`), `track_name`, `nogos`, `alternativeidx`.
- Returns: route summary (distance, elevation, duration) + GPX/GeoJSON data.
- GPX is already in `<trk>/<trkseg>/<trkpt>` format with elevation — no post-processing needed.

### Location Search — `mcp_brouter_search_location`

- Search by place name via Nominatim. Default country: Germany (`de`).
- Returns coordinates as `[longitude, latitude]`.
- Rate-limited to 1 request/second (handled automatically by the server).

### Map Rendering — `mcp_brouter_render_gpx_map`

- Renders a GPX file as PNG with OpenStreetMap tiles.
- Required: `gpx_path`, `output_path` (use **absolute paths** — the MCP server runs from `brouter-mcp/`).
- Optional: `width` (default 800), `height` (default 600), `line_color`, `line_width`.

### POI Search

- BRouter and Nominatim do not provide POI search.
- Use `remote_web_search` to find attractions, swimming spots, cafés, and events along the route.

## Points of Interest Categories

Use these emoji prefixes consistently in all output:

| Emoji | Category             | What to include                                                                                                      |
| ----- | -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 🏛️    | Sehenswürdigkeiten   | Castles, parks, historic buildings, museums, viewpoints, churches, memorials                                         |
| 🎨    | Moderne Kunst        | Galleries, sculpture parks, installations, street art, Ateliers. **Always highlight — user has a special interest.** |
| 🍺    | Einkehrmöglichkeiten | Cafés, beer gardens, restaurants. **Prioritize cafés with selbstgebackener Kuchen.**                                 |
| 🏊    | Badestellen          | Swimming spots at lakes along the route                                                                              |

## Weather

- Query forecast for the tour date and start location using `mcp_weather_weather_forecast`.
- Include: temperature range, precipitation probability, wind conditions.
- Warn if rain probability >50%, storms, or extreme temperatures (>35°C, <0°C).
- Suggest alternative dates or time windows if weather is unfavorable.

## Public Transit (Nahverkehr)

- **Home station**: S Blankenfelde (TF) Bhf (S2, RB24, RE5, RE7, RE8). Always use as origin/destination.
- Connections with 1–2 transfers are acceptable.
- Tools:
  - `mcp_berlin_transport_search_stops` — resolve stop IDs.
  - `mcp_berlin_transport_get_journeys` — plan connections from/to Blankenfelde.
  - `mcp_berlin_transport_get_departures` — check departure times.
- Always include: Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).

### Verification Rule

- **NEVER** claim specific transit lines, direct connections, or travel times without querying the API first.
- Resolve stop IDs via `mcp_berlin_transport_search_stops`, then verify connections via `mcp_berlin_transport_get_journeys`.
- Present only verified information: line names, transfer stations, number of changes, travel times.
- If the API is unavailable, explicitly state: ℹ️ Verbindungen nicht per API verifiziert.

## Events

- Search for current events along the route using `remote_web_search`.
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local event calendars.
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Chorin Musiksommer).

## File Structure

All tour files live under `touren/`:

```
touren/
├── README.md              # Tour catalog (index)
├── {tour-name}.md         # Individual tour descriptions
├── gpx/{tour-name}.gpx    # GPX tracks
└── img/{tour-name}.png    # Route map images
```

- File naming: descriptive kebab-case without `-runde` suffix, e.g., `spreewald.md`, `spreewald.gpx`.
- GPX and image paths in tour markdown are relative: `gpx/spreewald.gpx`, `img/spreewald.png`.

## Markdown Tour Description

### Required Sections (in order)

1. **Title**: `# {Tour-Name} ab {Start/Ziel}` (H1)
2. **Metadata table**: Distanz, Fahrzeit, Routentyp, Start/Ziel, GPX-Datei (clickable link)
3. **Tip box**: `> 🏛️/🌿/🌸 **Tipp:** ...` — one-line highlight
4. **Streckenverlauf**: Arrow-separated (`→`) overview, followed by map image: `![Name Karte](img/name.png)`
5. **Streckenabschnitte**: H3 per segment with distance, description, POI highlights using emoji prefixes
6. **Badestellen**: Swimming spots list (omit if none)
7. **Einkehrmöglichkeiten**: Food/drink stops summary
8. **Wetter**: Forecast for tour date — temperature, rain, wind. Warn if unfavorable.
9. **Veranstaltungen**: Events near the route (omit if none)
10. **Nahverkehrsanbindung**: Transit connections with verification status, bike transport note

### Segment Pattern

```markdown
### {N}. {Von} → {Nach} (ca. {X} km)

{Route description with path/street names in **bold**.}

🏛️ **{Name}** — {short description}
🎨 **{Name}** — {short description}
🍺 {Description of café/restaurant}
🏊 **{Name}** — {short description}
```

## Workflow

Execute these steps in order when the user requests a tour:

1. **Geocode** waypoints via `mcp_brouter_search_location`. Verify coordinates are in Brandenburg.
2. **Calculate route** via `mcp_brouter_calculate_route` with 3–6 waypoints. First = last for round trips.
3. **Save GPX**: Extract GPX XML from the response, save to `touren/gpx/{name}.gpx`.
4. **Render map**: Use `mcp_brouter_render_gpx_map` with absolute paths, save to `touren/img/{name}.png`.
5. **Query weather** forecast for tour date.
6. **Verify transit** connections from/to Blankenfelde via `mcp_berlin_transport_get_journeys`.
7. **Search events** along the route via `remote_web_search`.
8. **Write markdown** tour description to `touren/{name}.md`.
9. **Update index**: Add tour to `touren/README.md`.
10. **Present summary** to the user in German.
