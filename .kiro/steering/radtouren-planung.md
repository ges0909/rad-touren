---
inclusion: always
---

# Radtouren-Planung — Berlin/Brandenburg

Guide for planning, generating, and presenting cycling tours in the Berlin/Brandenburg region.

## Language

- All tour output (descriptions, highlights, summaries, markdown files) MUST be in **German**.
- Tool calls, code identifiers, and file names use English/kebab-case.

## Coordinate Convention

- Format: `[longitude, latitude]` — longitude first. Applies to all MCP tool calls.
- Scope: Berlin/Brandenburg. Tours start from locations reachable by public transit from Blankenfelde-Mahlow.
- Geocoding pitfall: `mcp_openroute_mcp_search_location_coordinates` may return locations outside Germany. Always verify coordinates fall within Berlin/Brandenburg (lat ~51.3–53.6, lon ~11.3–14.8). Use hardcoded coordinates for well-known places when results are unreliable.

## Routing

- Default `route_type`: `cycling-regular`. Only use `cycling-mountain` when explicitly requested.
- Prefer: designated Radwege, quiet side roads, waterfront paths.
- Avoid: Bundesstraßen (B-roads), heavily trafficked through-roads, highways.
- Use **5–7 intermediate waypoints** to steer routes along quiet paths.

### Round Trips (Rundtouren)

- Set `from_coordinates` = `to_coordinates` (same point).
- Define route shape entirely through `waypoints`.
- Choose start/end points with good public transit access (S-Bahn, Regionalbahn).
- **CRITICAL**: Waypoints must lie on or very near a mapped path in OpenStreetMap. The API returns 404 if a waypoint cannot be snapped to a cyclable way. Place waypoints on actual paths, intersections, or named places — never in unmapped forest, on water, or in parks without mapped paths.

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

## MCP Tool Usage

### Route Creation — `mcp_openroute_mcp_create_route_from_to`

- Required params: `route_type`, `from_coordinates`, `to_coordinates`.
- `waypoints`: required for round trips, recommended for all routes (5–7 points).
- Auto-generates GPX, HTML map, and PNG in `data/generated_routes/`.
- **Post-processing**: The API GPX uses `<rte>/<rtept>` format. Extract coordinates and reformat as `<trk>/<trkseg>/<trkpt>` GPX. Save to `gpx/`.
- Copy the auto-generated PNG to `img/` with a descriptive kebab-case name.
- **404 error handling**: A waypoint cannot be snapped to the road network. Move it to a nearby street coordinate and retry. Round trips (from=to) work fine when all waypoints are on roads.

### Location Search — `mcp_openroute_mcp_search_location_coordinates`

- Cross-check returned coordinates fall within Berlin/Brandenburg.
- Prefer hardcoded coordinates for well-known locations (Potsdam Hbf, Werder, KW, etc.).

### Points of Interest — `mcp_openroute_mcp_search_pois`

- Query with a bounding box along each route segment to find attractions, rest stops, swimming spots, restaurants, and art venues.

### Reachability — `mcp_openroute_mcp_get_reachable_area`

- Use to estimate feasible tour radius from a starting point.

### Known Trails — `mcp_openroute_mcp_search_known_routes`

- Switzerland only. Do not call for this region.

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

- **Home station**: Blankenfelde-Mahlow (S2, RE5, RE7). Always use as origin/destination.
- Connections with 1–2 transfers are acceptable.
- Tools:
  - `mcp_berlin_transport_search_stops` — resolve stop IDs.
  - `mcp_berlin_transport_get_journeys` — plan connections from/to Blankenfelde-Mahlow.
  - `mcp_berlin_transport_get_departures` — check departure times.
- Always include: Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).

### Verification Rule

- **NEVER** claim specific transit lines, direct connections, or travel times without querying the API first.
- Resolve stop IDs via `mcp_berlin_transport_search_stops`, then verify connections via `mcp_berlin_transport_get_journeys`.
- Present only verified information: line names, transfer stations, number of changes, travel times.
- If the API is unavailable, explicitly state that transit details are unverified.

## Events

- Search for current events along the route using `remote_web_search`.
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local event calendars.
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Potsdamer Schlössernacht).

## GPX Output Format

- GPX 1.1 with `<trk>/<trkseg>/<trkpt>` (NOT `<rte>/<rtept>`).
- `<metadata><name>`: tour name + approximate distance, e.g., `Havel-Schwielowsee-Runde ab Potsdam Hbf (~43 km)`.
- `<metadata><desc>`: key stops as arrow-separated list.
- `<trk><name>`: tour name without distance.
- File naming: descriptive kebab-case, e.g., `havel-schwielowsee-runde.gpx`.
- Save GPX to `gpx/`, PNG to `img/`.
- Suggest [brouter-web](https://brouter.de/brouter-web/) for manual route optimization.

## Markdown Tour Description

Save as `{tour-name}.md` at workspace root, matching the GPX base name.

### Required Sections (in order)

1. **Title**: `# {Tour-Name} ab {Start/Ziel}` (H1)
2. **Metadata table**: Distanz, Fahrzeit, Routentyp, Start/Ziel, GPX-Datei (clickable link to `gpx/` folder)
3. **Streckenverlauf**: Arrow-separated (`→`) overview of key stops, followed by route map image: `![Tour-Name Karte](img/tour-name.png)`
4. **Streckenabschnitte**: H3 per segment with distance, route description, POI highlights using emoji prefixes
5. **Badestellen**: Swimming spots list (omit if none)
6. **Einkehrmöglichkeiten**: Food/drink stops summary
7. **Wetter**: Forecast for tour date — temperature, rain, wind. Warn if unfavorable.
8. **Veranstaltungen**: Events near the route (omit if none)
9. **Nahverkehrsanbindung**: Transit connections, bike transport note

Do NOT include a separate "GPX & Karte" section.

### Segment Pattern

```markdown
### {N}. {Von} → {Nach} (ca. {X} km)

{Route description with street/path names in **bold**.}

🏛️ **{Name}** — {short description}
🎨 **{Name}** — {short description}
🍺 {Description of café/restaurant}
🏊 **{Name}** — {short description}
```

## Workflow

Execute these steps in order when the user requests a tour:

1. **Geocode** start/end and waypoint locations. Verify coordinates are in Brandenburg and on the road network.
2. **Create route** via `mcp_openroute_mcp_create_route_from_to` with 5–7 waypoints. For round trips, set from=to.
3. **Handle 404**: Adjust waypoints to nearby street coordinates and retry.
4. **Convert GPX**: Extract trackpoints, reformat `<rte>/<rtept>` → `<trk>/<trkseg>/<trkpt>`, save to `gpx/`.
5. **Copy PNG** to `img/` with descriptive name.
6. **Search POIs** along route segments via `mcp_openroute_mcp_search_pois`.
7. **Query weather** forecast for tour date.
8. **Verify transit** connections from/to Blankenfelde-Mahlow via API.
9. **Search events** along the route.
10. **Write markdown** tour description at workspace root with embedded map image.
11. **Present summary** to the user in German.
