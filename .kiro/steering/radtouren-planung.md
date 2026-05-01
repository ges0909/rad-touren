---
inclusion: always
---

# Radtouren-Planung — Berlin/Brandenburg

Plan, generate, and present cycling day-trip tours in the Berlin/Brandenburg region.

## Language

- All user-facing output (tour markdown, descriptions, summaries, chat responses about tours): **German**.
- Tool calls, code identifiers, file names, GPX `track_name` values: **English/kebab-case**.

## Geographic Scope

- Bounding box: lat 51.3–53.6, lon 11.3–14.8.
- All tours must be reachable by public transit from **S Blankenfelde (TF) Bhf**.
- After every geocode call, verify coordinates fall within bounds. If outside, reject and re-geocode with a more specific query.

## Coordinate Convention

**CRITICAL**: All MCP tool calls use **[longitude, latitude]** — longitude first. This applies to `mcp_brouter_calculate_route` waypoints and all other coordinate parameters. Swapping the order produces routes in the wrong location.

## Routing Rules

Use `mcp_brouter_calculate_route` with `profile=trekking` (default).

- Shape routes with **3–6 waypoints total** (including start/end).
- **Round trips (Rundtouren)**: first and last waypoint MUST have identical coordinates.
- Start/end points: choose locations near train stations with S-Bahn/Regionalbahn access.
- Waypoints must form a logical loop — no backtracking or unnecessary detours.

### Well-Known Regional Cycling Routes

Reference these when selecting waypoints and writing segment descriptions:

| Route             | Area                                  |
| ----------------- | ------------------------------------- |
| Havelradweg       | Potsdam → Werder → Brandenburg        |
| Europaradweg R1   | Through Potsdam and Werder            |
| Berliner Mauerweg | Former Berlin Wall loop               |
| Spreeradweg       | Along the Spree through Berlin        |
| Dahme-Radweg      | South of Berlin along the Dahme       |
| Oder-Havel-Radweg | North of Berlin                       |
| Tour Brandenburg  | Long-distance loop around Brandenburg |
| Gurkenradweg      | Through the Spreewald                 |

## MCP Tool Reference

### `mcp_brouter_search_location`

Geocode place names via Nominatim. Default `country_code=de`. Returns coordinates as `[longitude, latitude]`. Rate-limited to 1 req/s (handled by server).

### `mcp_brouter_calculate_route`

- **Required**: `waypoints` — list of `[lon, lat]` pairs (minimum 2).
- **Optional**: `profile` (default `trekking`), `format` (`gpx`|`geojson`), `track_name`, `nogos`, `alternativeidx`.
- **Returns**: distance, elevation gain/loss, estimated duration, and GPX/GeoJSON data. GPX contains `<trk>/<trkseg>/<trkpt>` with elevation — no post-processing needed.

### `mcp_brouter_render_gpx_map`

Renders a GPX track as a PNG map with OSM tiles. Defaults: 800×600 px.

**CRITICAL**: Both `gpx_path` and `output_path` MUST be **absolute paths**. The MCP server runs from `mcp/brouter/`, so relative paths resolve to the wrong location.

### `mcp_brouter_render_elevation_profile`

Renders an elevation profile chart as PNG from a GPX track. Reports min/max elevation, total ascent/descent. Same **absolute path requirement** as `render_gpx_map`.

### `mcp_overpass_search_pois_along_route`

Finds POIs along a GPX route via OpenStreetMap/Overpass API. Requires an **absolute** GPX path.

Available presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`.

Supplement with `remote_web_search` for events, opening hours, and details not in OSM.

### `mcp_open_meteo_weather_forecast`

Query weather forecast for the tour date using start-location coordinates.

### VBB Transport Tools

- `mcp_vbb_search_stops` — resolve stop names to stop IDs.
- `mcp_vbb_get_journeys` — plan connections between two stops.
- `mcp_vbb_get_departures` — list upcoming departures at a stop.

## Points of Interest

Use these emoji prefixes consistently in all tour output:

| Emoji | Category             | Guidance                                                                                                                    |
| ----- | -------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 🏛️    | Sehenswürdigkeiten   | Castles, parks, historic buildings, museums, viewpoints, churches, memorials                                                |
| 🎨    | Moderne Kunst        | Galleries, sculpture parks, installations, street art, ateliers. **Always highlight — user has a special interest in art.** |
| 🍺    | Einkehrmöglichkeiten | Cafés, beer gardens, restaurants. **Prioritize cafés with selbstgebackener Kuchen.**                                        |
| 🏊    | Badestellen          | Swimming spots at lakes along the route                                                                                     |

## Weather Rules

- Every tour MUST include: temperature range, precipitation probability, wind speed/direction.
- Warn explicitly if: rain probability >50 %, storms forecast, temperature >35 °C or <0 °C.
- If weather is unfavorable, suggest alternative dates or time windows.

## Public Transit Rules

- **Home station**: S Blankenfelde (TF) Bhf (lines: S2, RB24, RE5, RE7, RE8). Always use as origin and destination for journey planning.
- Connections with 1–2 transfers are acceptable.
- Every tour MUST include the bike-transport note: `> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).`

### Transit Verification

**NEVER** claim specific line names, direct connections, or travel times without querying the VBB API first.

1. Resolve stop IDs via `mcp_vbb_search_stops`.
2. Query connections via `mcp_vbb_get_journeys`.
3. Present only API-verified information: line names, transfer stations, number of changes, travel times.
4. If the API is unavailable or returns errors, state: `ℹ️ Verbindungen nicht per API verifiziert.`

## Events

- Search for current events along the route using `remote_web_search`.
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local event calendars.
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Chorin Musiksommer).
- If no events found, include the section with a note that none were found.

## File Structure

All tour files live under `touren/`:

```
touren/
├── README.md                    # Tour catalog index
├── {tour-name}.md               # Tour description
├── gpx/{tour-name}.gpx          # GPX track
├── img/{tour-name}.png          # Route map image
└── img/{tour-name}-elevation.png # Elevation profile image
```

- File naming: descriptive kebab-case, no `-runde` suffix. Example: `spreewald.md`, `spreewald.gpx`.
- Paths inside tour markdown are **relative**: `gpx/spreewald.gpx`, `img/spreewald.png`.

## Tour Markdown Template

Every tour file MUST contain these sections in this exact order, separated by `---` horizontal rules.

### 1. Title

```markdown
# {Tour-Name}-Runde ab {Start/Ziel}
```

### 2. Metadata Block

Bold key-value pairs, one per line (not a table):

```markdown
**Distanz:** ~{X} km ({X} km lt. BRouter)
**Fahrzeit:** ca. {X}–{Y} Std. (ohne Pausen)
**Routentyp:** Rundtour, {terrain}
**Start/Ziel:** {Station name}
**GPX-Datei:** [gpx/{name}.gpx](gpx/{name}.gpx)
```

### 3. Tip Box

```markdown
> {emoji} **Tipp:** {one-line highlight of the tour}
```

Choose emoji by tour theme: 🏛️ (culture), 🌿 (nature), 🌸 (seasonal), 🌊 (water/lakes), 🌲 (forest).

### 4. Streckenverlauf

Arrow-separated waypoint overview, followed by the route map and elevation profile images:

```markdown
## Streckenverlauf

{Start} → {Waypoint 1} → {Waypoint 2} → … → {Start}

![{Tour-Name} Karte](img/{name}.png)

![Höhenprofil](img/{name}-elevation.png)
```

### 5. Streckenabschnitte

One H3 subsection per segment. Include only POI types that actually exist along that segment:

```markdown
### {N}. {Von} → {Nach} (ca. {X} km)

{Description with path/street names in **bold**. Mention named cycling routes where applicable.}

🏛️ **{Name}** — {short description}
🎨 **{Name}** — {short description}
🍺 {Café/restaurant name} — {short description}
🏊 **{Name}** — {short description}
```

### 6. Badestellen

Omit section entirely if no swimming spots along the route.

```markdown
## Badestellen

- 🏊 **{Name}** — {description}
```

### 7. Einkehrmöglichkeiten

Summary of all food/drink stops mentioned in the segments.

### 8. Wetter

```markdown
## Wetter am {Wochentag}, {Datum}

> ℹ️ _Zuletzt geprüft: {date}. Vor der Tour aktuelles Wetter prüfen._

{weather-emoji} **{Summary}**

|                |                                |
| -------------- | ------------------------------ |
| **Temperatur** | {min}–{max}°C                  |
| **Regen**      | {mm} ({X}% Wahrscheinlichkeit) |
| **Wind**       | ~{X} km/h {direction}          |
| **Wetterlage** | {description}                  |
```

Add warnings or recommendations below the table when conditions are notable (heat, rain, wind).

### 9. Veranstaltungen

Events near the route. Include section with a note if none found.

### 10. Nahverkehrsanbindung

```markdown
## Nahverkehrsanbindung

> ℹ️ _Verbindungen verifiziert für {date}. Vor der Tour aktuelle Fahrpläne prüfen._

**Hinfahrt:**
Ab **S Blankenfelde (TF) Bhf** → {line} bis {station} → {line} bis **{Ziel}**

- Abfahrt: {HH:MM} Uhr ab Blankenfelde → Ankunft {HH:MM} Uhr in {Ziel}
- {N} Umstieg(e), {X} Min.

**Rückfahrt:**
Ab **{Start}** → {line} bis {station} → {line} bis **S Blankenfelde (TF) Bhf**

- Abfahrt: {HH:MM} Uhr ab {Start} → Ankunft {HH:MM} Uhr in Blankenfelde
- {N} Umstieg(e), {X} Min.

> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).
```

## Tour Catalog Index (`touren/README.md`)

Table format with columns: Tour (linked, with theme emoji prefix), Distanz, Fahrzeit, Region. File ends with the bike-transport note.

When adding a tour, **append** a new row to the existing table. Do not rewrite the entire file.

## Workflow

Execute these steps in order when the user requests a new tour:

1. **Geocode** waypoints via `mcp_brouter_search_location`. Verify all coordinates are within bounds.
2. **Calculate route** via `mcp_brouter_calculate_route` with 3–6 waypoints. First = last for round trips.
3. **Save GPX** to `touren/gpx/{name}.gpx`. Write the GPX XML directly from the route response.
4. **Render map** via `mcp_brouter_render_gpx_map` (absolute paths). Save to `touren/img/{name}.png`.
5. **Render elevation profile** via `mcp_brouter_render_elevation_profile` (absolute paths). Save to `touren/img/{name}-elevation.png`.
6. **Search POIs** via `mcp_overpass_search_pois_along_route` with presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`.
7. **Query weather** for the tour date and start-location coordinates.
8. **Verify transit** from/to S Blankenfelde (TF) Bhf via VBB tools.
9. **Search events** along the route via `remote_web_search`.
10. **Write tour markdown** to `touren/{name}.md` following the template.
11. **Update index** — append a row to `touren/README.md`.
12. **Present summary** to the user in German.

### Error Handling

- **Geocode returns no results**: retry with a more specific or alternative place name. If still failing, ask the user for clarification.
- **Route calculation fails**: check waypoint order and coordinates. Try removing or adjusting problematic intermediate waypoints.
- **VBB API unavailable**: include the fallback note `ℹ️ Verbindungen nicht per API verifiziert.` and skip specific line/time claims.
- **POI search returns empty**: note the absence in the relevant section; do not fabricate POIs.
- **Weather API unavailable**: state `ℹ️ Wetterdaten nicht verfügbar.` in the weather section.

## Tour Lifecycle

Tours are **templates and inspiration**. GPX tracks and map images are stable, but date-dependent sections must be refreshed before riding:

| Section              | Tool to refresh                   | Reason                                |
| -------------------- | --------------------------------- | ------------------------------------- |
| Wetter               | `mcp_open_meteo_weather_forecast` | Forecasts change daily                |
| Veranstaltungen      | `remote_web_search`               | Events are seasonal                   |
| Nahverkehrsanbindung | `mcp_vbb_get_journeys`            | Schedules change per timetable period |

When refreshing, update the `ℹ️ Zuletzt geprüft: {date}` timestamp. If a section cannot be verified, mark it: `ℹ️ Nicht verifiziert.`
