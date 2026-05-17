---
inclusion: fileMatch
fileMatchPattern: "trips/bike/**"
---

# Cycling Tour Planning — Berlin/Brandenburg

Plan, generate, and present cycling day-trip tours in the Berlin/Brandenburg region.

## Language Rules

Defer to `user-preferences.md`. Summary: user-facing output in **German**, code/filenames/GPX in **English/kebab-case**.

## Geographic Scope

- Bounding box: lat 51.3–53.6, lon 11.3–14.8
- All tours reachable by public transit from **S Blankenfelde (TF) Bhf**
- After every geocode call, verify coordinates fall within bounds. Reject and re-geocode with a more specific query if outside.

## Home Base

- **Station**: S Blankenfelde (TF) Bhf
- **Lines**: S2, RB24, RE5, RE7, RE8
- **Departure**: ~09:00 Uhr
- All Berlin/Brandenburg tours must be reachable from this station.

## Critical Conventions (Never Violate)

Content integrity rules (no fabrication, source attribution, deduplication) are defined in `user-preferences.md`. Additional cycling-specific rules:

1. **Coordinate order**: All MCP tool calls use **[longitude, latitude]** — longitude first.
2. **Absolute paths**: `render_gpx_map`, `render_elevation_profile`, and `search_pois_along_route` require **absolute file paths**. MCP servers run from subdirectories — relative paths resolve incorrectly.
3. **Overpass rate limit**: Query POI presets **sequentially** (one at a time). Never parallelize.
4. **Transit verification**: Never claim line names, connections, or travel times without querying VBB API first.

## Routing

Use `mcp_brouter_calculate_route` with `profile=trekking` (default).

- **3–6 waypoints** total (including start/end)
- **Round trips**: first and last waypoint MUST have identical coordinates
- Start/end near train stations with S-Bahn/Regionalbahn access
- Waypoints form a logical loop — no backtracking
- Place waypoints on **through-roads or intersections**, never dead-end streets (BRouter snaps to nearest road segment; a cul-de-sac creates a spur)

### Spur Removal (Post-Processing)

After saving a GPX file, check for spurs (out-and-back segments from dead-end snapping):

- **Detection**: `point[i] ≈ point[j]` (distance < 15 m) with `j > i + 4`
- **Fix**: Remove points `i+1` through `j-1`, re-save GPX, update distance in tour markdown

### Regional Cycling Routes Reference

Use when selecting waypoints and writing segment descriptions:

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

## Allowed MCP Servers

Use **only** these MCP servers for cycling tour planning. Do not use other available servers unless explicitly requested.

| Server          | Prefix                  | Purpose                                     |
| --------------- | ----------------------- | ------------------------------------------- |
| brouter         | `mcp_brouter_*`         | Route calculation, geocoding, map rendering |
| overpass        | `mcp_overpass_*`        | POI search along routes                     |
| open-meteo      | `mcp_open_meteo_*`      | Weather forecast                            |
| vbb             | `mcp_vbb_*`             | Public transit connections                  |
| waymarkedtrails | `mcp_waymarkedtrails_*` | Discover marked cycling routes              |

## MCP Tool Reference

### Routing & Maps (`mcp_brouter_*`)

| Tool                       | Key Parameters & Notes                                                                                             |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `search_location`          | Geocode via Nominatim. Default `country_code=de`. Returns `[lon, lat]`. Rate-limited 1 req/s.                      |
| `calculate_route`          | Required: `waypoints` (`[[lon,lat],...]`). Optional: `profile`, `format`, `track_name`, `nogos`, `alternativeidx`. |
| `render_gpx_map`           | 800×600 default. Optional `pois` list for markers. **Absolute paths required.**                                    |
| `render_elevation_profile` | Reports min/max elevation, total ascent/descent. **Absolute paths required.**                                      |

### POIs (`mcp_overpass_*`)

| Tool                      | Key Parameters & Notes                                                                                                                       |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_pois_along_route` | **Absolute GPX path required.** Presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. Query sequentially. |

### Weather (`mcp_open_meteo_*`)

| Tool               | Key Parameters & Notes                        |
| ------------------ | --------------------------------------------- |
| `weather_forecast` | Use start-location coords. Specify tour date. |

### Transit (`mcp_vbb_*`)

| Tool             | Key Parameters & Notes                        |
| ---------------- | --------------------------------------------- |
| `search_stops`   | Resolve stop names to IDs.                    |
| `get_journeys`   | Plan connections. Returns Regionaltarif fare. |
| `get_departures` | Upcoming departures from a stop.              |

## Points of Interest

POI categories and interest priorities are defined in `user-preferences.md`. For map rendering, use these Overpass-to-emoji mappings:

| Emoji | Overpass categories                                |
| ----- | -------------------------------------------------- |
| 🏛️    | museum, castle, memorial, ruins, church, viewpoint |
| 🎨    | artwork, gallery                                   |
| 🍺    | beer_garden, cafe, restaurant                      |
| 🏊    | swimming                                           |

Pass Overpass category names directly to `render_gpx_map` `pois` parameter.

### POI Curation for Map Rendering

- Select ~15–25 POIs for the map
- Prioritize by interest order from `user-preferences.md`
- Deduplicate per `user-preferences.md` rules (200 m radius)

## Weather

- Every tour MUST include: temperature range, precipitation probability, wind speed/direction
- Warn if: rain probability > 50%, storms forecast, temperature > 35 °C or < 0 °C
- If unfavorable, suggest alternative dates or time windows

## Public Transit

- **Home station**: S Blankenfelde (TF) Bhf (lines: S2, RB24, RE5, RE7, RE8)
- **Default departure**: ~09:00 ab Blankenfelde
- **Group**: per `user-preferences.md` (2 persons + 2 bicycles)
- 1–2 transfers acceptable
- Every tour MUST include: `> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).`

### Transit Verification Steps

1. Resolve stop IDs via `search_stops`
2. Query connections via `get_journeys`
3. Present only API-verified information
4. If API unavailable: `ℹ️ Verbindungen nicht per API verifiziert.`

### Disruption Check (Schienenersatzverkehr)

Before finalizing transit, check for disruptions on **all lines and segments** used:

1. `remote_web_search` for `S-Bahn Berlin Störungen Schienenersatzverkehr` and specific lines used
2. `remote_web_search` for `"S-Bahn Berlin Bauarbeiten Störungen {tour date month/year}"`
3. Fetch `https://sbahn.berlin/en/plan-a-journey/timetable-changes/` for replacement services on relevant lines

**If SEV active on any segment:**

- Note affected segment and duration in Nahverkehrsanbindung section
- Add: `> ⚠️ **Schienenersatzverkehr:** {Linie} zwischen {A} und {B} bis {Datum}. Ersatzbusse fahren — zusätzliche Reisezeit einplanen.`
- Add: `> 🚲⚠️ In Ersatzbussen ist die Fahrradmitnahme in der Regel nicht möglich. Alternative Verbindung ohne SEV-Abschnitt prüfen.`
- Suggest alternative connection avoiding SEV segment
- If no bike-friendly alternative exists, suggest alternative date

**If no disruptions found**: No warning needed.

## Events

- Search via `remote_web_search` for events along the route on the tour date
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local calendars
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Chorin Musiksommer)
- If none found, include section with a note stating no events were found

## File Structure

All tour files live under `trips/bike/`:

```
trips/bike/
├── README.md                     # Tour catalog index
├── {tour-name}/
│   ├── index.md                  # Tour description
│   ├── gpx/{tour-name}.gpx      # GPX track
│   └── img/
│       ├── {tour-name}.png           # Route map image
│       └── {tour-name}-elevation.png # Elevation profile image
```

- Naming: descriptive kebab-case, no `-runde` suffix. Example: `spreewald/index.md`, `spreewald/gpx/spreewald.gpx`
- Paths inside tour markdown are **relative**: `gpx/spreewald.gpx`, `img/spreewald.png`

## Output Template

See `bike-template.md` for the full markdown template structure including fare tables.

## Tour Catalog Index (`trips/bike/README.md`)

Table with columns: Tour (linked, theme emoji prefix), Distanz, Fahrzeit, Region. Ends with bike-transport note.

When adding a tour, **append** a row to the existing table. Do not rewrite the file.

## Workflow

Execute in order when the user requests a new tour:

### Phase 1: Route Generation

1. **Geocode** waypoints via `search_location`. Verify coordinates within bounds.
2. **Calculate route** via `calculate_route` (3–6 waypoints, first = last for round trips).
3. **Save GPX** to `trips/bike/{name}/gpx/{name}.gpx`.
4. **Check for spurs** in GPX. Remove and re-save if detected.

### Phase 2: Enrichment

5. **Search POIs** via `search_pois_along_route` with presets `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst` — **sequentially, one at a time**.
6. **Render map** via `render_gpx_map` with curated POI markers (~15–25, deduplicated). Save to `trips/bike/{name}/img/{name}.png`.
7. **Render elevation** via `render_elevation_profile`. Save to `trips/bike/{name}/img/{name}-elevation.png`.
8. **Query weather** for tour date at start-location coordinates.
9. **Verify transit** from/to S Blankenfelde (TF) Bhf via VBB tools.
10. **Check disruptions** (see Disruption Check section above).
11. **Search events** via `remote_web_search`.

### Phase 3: Output

12. **Write tour markdown** to `trips/bike/{name}/index.md` following the template exactly.
13. **Update index** — append row to `trips/bike/README.md`.
14. **Present summary** to user in German.

## Error Handling

| Failure                    | Action                                                                  |
| -------------------------- | ----------------------------------------------------------------------- |
| Geocode returns no results | Retry with more specific name. If still failing, ask user.              |
| Route calculation fails    | Check waypoint order/coordinates. Adjust intermediate waypoints.        |
| VBB API unavailable        | Add `ℹ️ Verbindungen nicht per API verifiziert.` Skip line/time claims. |
| POI search empty           | Note absence in section. Do not fabricate POIs.                         |
| Weather API unavailable    | Add `ℹ️ Wetterdaten nicht verfügbar.`                                   |

## Tour Lifecycle (Refreshing Existing Tours)

GPX tracks and map images are stable. Date-dependent sections need refreshing:

| Section              | Tool                | Reason                                |
| -------------------- | ------------------- | ------------------------------------- |
| Wetter               | `weather_forecast`  | Forecasts change daily                |
| Veranstaltungen      | `remote_web_search` | Events are seasonal                   |
| Nahverkehrsanbindung | `get_journeys`      | Schedules change per timetable period |

When refreshing, update the `ℹ️ Zuletzt geprüft: {date}` timestamp. If unverifiable: `ℹ️ Nicht verifiziert.`
