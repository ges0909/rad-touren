---
inclusion: always
---

# Radtouren-Planung — Berlin/Brandenburg

Planning, generating, and presenting cycling day-trip tours in the Berlin/Brandenburg region.

## Language Rules

- All user-facing tour output (markdown files, descriptions, summaries, chat responses about tours) MUST be in **German**.
- Tool calls, code identifiers, file names, and GPX `track_name` values use English/kebab-case.

## Geographic Scope

- Region: Berlin/Brandenburg (lat ~51.3–53.6, lon ~11.3–14.8).
- All tours start from locations reachable by public transit from **S Blankenfelde (TF) Bhf**.
- After geocoding any waypoint, verify its coordinates fall within the region bounds above. Reject and re-geocode if outside.

## Coordinate Convention

All MCP tool calls use `[longitude, latitude]` — longitude first. This applies to `mcp_brouter_calculate_route` waypoints and any other coordinate parameters.

## Routing

Use `mcp_brouter_calculate_route` with `profile=trekking` (default). The trekking profile prefers designated cycle paths, regional cycling routes, and quiet roads automatically.

- Define routes with **3–6 intermediate waypoints** to shape the path.
- For **round trips (Rundtouren)**: first and last waypoint MUST be identical coordinates.
- Choose start/end points near train stations with good S-Bahn/Regionalbahn access.
- Verify waypoints form a logical loop — no backtracking or unnecessary detours.

### Well-Known Regional Cycling Routes

Reference these when selecting waypoints and describing route segments:

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

Geocode place names via Nominatim. Default country: `de`. Returns `[longitude, latitude]`. Rate-limited to 1 req/s (handled by server).

### `mcp_brouter_calculate_route`

- Required: `waypoints` — list of `[lon, lat]` pairs (minimum 2).
- Optional: `profile` (default `trekking`), `format` (`gpx`/`geojson`), `track_name`, `nogos`, `alternativeidx`.
- Returns: distance, elevation, duration + GPX/GeoJSON. GPX uses `<trk>/<trkseg>/<trkpt>` with elevation — no post-processing needed.

### `mcp_brouter_render_gpx_map`

Renders GPX as PNG with OSM tiles. Both `gpx_path` and `output_path` MUST be **absolute paths** (the MCP server runs from `mcp/brouter/`, so relative paths resolve incorrectly). Defaults: 800×600px.

### POI Search

BRouter and Nominatim have no POI search. Use `remote_web_search` to find attractions, swimming spots, cafés, and events along the route.

### `mcp_open_meteo_weather_forecast`

Query forecast for the tour date and start location coordinates.

### VBB Transport Tools

- `mcp_vbb_search_stops` — resolve stop names to stop IDs.
- `mcp_vbb_get_journeys` — plan connections between stops.
- `mcp_vbb_get_departures` — check departure times at a stop.

## Points of Interest

Use these emoji prefixes consistently in all tour output:

| Emoji | Category             | Guidance                                                                                                                    |
| ----- | -------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 🏛️    | Sehenswürdigkeiten   | Castles, parks, historic buildings, museums, viewpoints, churches, memorials                                                |
| 🎨    | Moderne Kunst        | Galleries, sculpture parks, installations, street art, ateliers. **Always highlight — user has a special interest in art.** |
| 🍺    | Einkehrmöglichkeiten | Cafés, beer gardens, restaurants. **Prioritize cafés with selbstgebackener Kuchen.**                                        |
| 🏊    | Badestellen          | Swimming spots at lakes along the route                                                                                     |

## Weather

- Include in every tour: temperature range, precipitation probability, wind speed/direction.
- Warn explicitly if: rain probability >50%, storms forecast, temperature >35°C or <0°C.
- If weather is unfavorable, suggest alternative dates or time windows.

## Public Transit (Nahverkehr)

- **Home station**: S Blankenfelde (TF) Bhf (lines: S2, RB24, RE5, RE7, RE8). Always use as origin and destination.
- Connections with 1–2 transfers are acceptable.
- Every tour MUST include: `> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).`

### Transit Verification Rule

**NEVER** claim specific line names, direct connections, or travel times without querying the API first.

1. Resolve stop IDs via `mcp_vbb_search_stops`.
2. Verify connections via `mcp_vbb_get_journeys`.
3. Present only API-verified information: line names, transfer stations, number of changes, travel times.
4. If the API is unavailable, state: `ℹ️ Verbindungen nicht per API verifiziert.`

## Events

- Search for current events along the route using `remote_web_search`.
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local event calendars.
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Chorin Musiksommer).
- If no events found, include the section with a note that no events were found.

## File Structure

All tour files live under `touren/`:

```
touren/
├── README.md              # Tour catalog (index)
├── {tour-name}.md         # Individual tour description
├── gpx/{tour-name}.gpx    # GPX track
└── img/{tour-name}.png    # Route map image
```

- File naming: descriptive kebab-case, no `-runde` suffix. Example: `spreewald.md`, `spreewald.gpx`.
- Paths inside tour markdown are relative: `gpx/spreewald.gpx`, `img/spreewald.png`.

## Tour Markdown Template

Every tour markdown file MUST contain these sections in this order:

### 1. Title (H1)

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

Use 🏛️, 🌿, 🌸, or 🌊 depending on the tour's main theme.

### 4. Streckenverlauf

Arrow-separated waypoint overview followed by the map image:

```markdown
## Streckenverlauf

{Start} → {Waypoint 1} → {Waypoint 2} → … → {Start}

![{Tour-Name} Karte](img/{name}.png)
```

### 5. Streckenabschnitte

One H3 subsection per segment:

```markdown
### {N}. {Von} → {Nach} (ca. {X} km)

{Description with path/street names in **bold**. Mention named cycling routes where applicable.}

🏛️ **{Name}** — {short description}
🎨 **{Name}** — {short description}
🍺 {Café/restaurant description}
🏊 **{Name}** — {short description}
```

Not every segment needs all POI types. Include only what exists along that segment.

### 6. Badestellen

List of swimming spots. Omit section entirely if none along the route.

```markdown
## Badestellen

- 🏊 **{Name}** — {description}
```

### 7. Einkehrmöglichkeiten

Summary of food/drink stops from all segments.

### 8. Wetter

```markdown
## Wetter am {Wochentag}, {Datum}

> ℹ️ _Zuletzt geprüft: {date}. Vor der Tour aktuelles Wetter prüfen._

{emoji} **{Summary}**

|                |                                |
| -------------- | ------------------------------ |
| **Temperatur** | {min}–{max}°C                  |
| **Regen**      | {mm} ({X}% Wahrscheinlichkeit) |
| **Wind**       | ~{X} km/h {direction}          |
| **Wetterlage** | {description}                  |
```

### 9. Veranstaltungen

Events near the route. Omit section if none found.

### 10. Nahverkehrsanbindung

```markdown
## Nahverkehrsanbindung

> ℹ️ _Verbindungen verifiziert für {date}. Vor der Tour aktuelle Fahrpläne prüfen._

**Hinfahrt:**
{Verified connection details}

**Rückfahrt:**
{Verified connection details}

> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).
```

## Tour Catalog Index (`touren/README.md`)

The index uses a table with columns: Tour (linked), Distanz, Fahrzeit, Region. Each tour row uses a theme emoji prefix. The file ends with the bike transport note.

When adding a tour, append a new row to the existing table. Do not rewrite the entire file.

## Workflow

Execute these steps in order when the user requests a new tour:

1. **Geocode** waypoints via `mcp_brouter_search_location`. Verify all coordinates are within Brandenburg bounds.
2. **Calculate route** via `mcp_brouter_calculate_route` with 3–6 waypoints. First = last for round trips.
3. **Save GPX** to `touren/gpx/{name}.gpx`. Extract the GPX XML directly from the route response.
4. **Render map** via `mcp_brouter_render_gpx_map` with absolute paths. Save to `touren/img/{name}.png`.
5. **Query weather** for the tour date and start location.
6. **Verify transit** from/to S Blankenfelde (TF) Bhf via `mcp_vbb_get_journeys`.
7. **Search events** along the route via `remote_web_search`.
8. **Write tour markdown** to `touren/{name}.md` following the template above.
9. **Update index** — append a row to `touren/README.md`.
10. **Present summary** to the user in German.

## Tour Lifecycle

Tours serve as **templates and inspiration**. GPX tracks and map images are stable, but date-dependent sections must be refreshed before riding:

| Section              | Tool to refresh                   | Why                                   |
| -------------------- | --------------------------------- | ------------------------------------- |
| Wetter               | `mcp_open_meteo_weather_forecast` | Forecasts change daily                |
| Veranstaltungen      | `remote_web_search`               | Events are seasonal                   |
| Nahverkehrsanbindung | `mcp_vbb_get_journeys`            | Schedules change per timetable period |

When refreshing, update the `ℹ️ Zuletzt geprüft: {date}` timestamp. If a section cannot be verified, mark it: `ℹ️ Nicht verifiziert.`
