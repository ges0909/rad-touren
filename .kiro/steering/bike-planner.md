---
inclusion: fileMatch
fileMatchPattern: "trips/bike/**"
---

# Bike Tour Planner — Berlin/Brandenburg

Rules for planning, generating, and presenting cycling day-trip tours in the Berlin/Brandenburg region. Read alongside `user-preferences.md` (personal defaults, content integrity, interests) and `bike-template.md` (output format).

## Language

User-facing output in **German**. Code, filenames, GPX metadata, and MCP parameters in **English/kebab-case**. See `user-preferences.md` for full language rules.

## Geographic Scope

- Bounding box: lat 51.3–53.6, lon 11.3–14.8
- All tours must be reachable by public transit from **S Blankenfelde (TF) Bhf**
- After every geocode call, verify coordinates fall within bounds. If outside, re-geocode with a more specific query.

## Home Base

| Field     | Value                   |
| --------- | ----------------------- |
| Station   | S Blankenfelde (TF) Bhf |
| Lines     | S2, RB24, RE5, RE7, RE8 |
| Departure | ~09:00 Uhr              |
| Group     | 2 persons + 2 bicycles  |

## Non-Negotiable Rules

These rules are hard constraints. Violating any of them produces incorrect output.

1. **Coordinate order**: All MCP tool calls use **[longitude, latitude]** — longitude first, always.
2. **Absolute paths**: `render_gpx_map`, `render_elevation_profile`, and `search_pois_along_route` require **absolute file paths**. MCP servers run from subdirectories — relative paths resolve incorrectly.
3. **Overpass rate limit**: Query POI presets **sequentially**, one call at a time. Never parallelize Overpass calls.
4. **Transit verification**: Never state line names, connections, or travel times without querying the VBB API. If the API is unavailable, say so explicitly.
5. **Map–POI sync**: Every POI mentioned in the tour text MUST appear as a marker on the map. If POIs change after the map is rendered, re-render.
6. **Seasonal awareness**: For every major POI, verify opening days, advance booking requirements, and seasonal closures. Flag required advance booking with `⚠️ vorab buchen`.
7. **No fabrication**: Present only data obtained from API results or web search. If data is unavailable, state it explicitly. See `user-preferences.md` for full content integrity rules.

## Allowed MCP Servers

Use **only** these servers for cycling tour planning. Do not invoke other available servers unless explicitly asked.

| Server          | Prefix                  | Purpose                                     |
| --------------- | ----------------------- | ------------------------------------------- |
| brouter         | `mcp_brouter_*`         | Route calculation, geocoding, map rendering |
| overpass        | `mcp_overpass_*`        | POI search along routes                     |
| open-meteo      | `mcp_open_meteo_*`      | Weather forecast                            |
| vbb             | `mcp_vbb_*`             | Public transit connections                  |
| waymarkedtrails | `mcp_waymarkedtrails_*` | Discover marked cycling/hiking routes       |

## MCP Tool Reference

### Routing & Maps (`mcp_brouter_*`)

| Tool                       | Key Parameters & Notes                                                                                                                                                                                                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_location`          | Geocode via Nominatim. Default `country_code=de`. Returns `[lon, lat]`. Rate-limited: 1 req/s.                                                                                                                                                                                                    |
| `calculate_route`          | Required: `waypoints` (`[[lon,lat],...]`). Default `profile=trekking`. Other profiles: `fastbike`, `safety`, `shortest`, `trekking-noferries`, `trekking-nosteps`, `trekking-steep`, `trekking-ignore-cr`. Optional: `track_name`, `nogos`, `alternativeidx` (0–3).                               |
| `render_gpx_map`           | 800×600 default. Optional `pois` list for markers. **Absolute paths required.** Valid POI `category` values: `museum`, `castle`, `memorial`, `ruins`, `church`, `viewpoint`, `artwork`, `gallery`, `beer_garden`, `cafe`, `restaurant`, `swimming`, `bicycle_repair`, `drinking_water`, `picnic`. |
| `render_elevation_profile` | Reports min/max elevation, total ascent/descent. **Absolute paths required.**                                                                                                                                                                                                                     |

### POIs (`mcp_overpass_*`)

| Tool                      | Key Parameters & Notes                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_pois_along_route` | **Absolute GPX path required.** Presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. Call sequentially — never in parallel. |

### Weather (`mcp_open_meteo_*`)

| Tool               | Notes                                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `weather_forecast` | Use start-location coordinates. Target the tour date via `forecast_days`.                                              |
| `geocoding`        | Alternative to BRouter `search_location` when only coordinates are needed; does not count toward Nominatim rate limit. |

### Transit (`mcp_vbb_*`)

| Tool             | Notes                                         |
| ---------------- | --------------------------------------------- |
| `search_stops`   | Resolve stop names to IDs before other calls. |
| `get_journeys`   | Plan connections. Returns Regionaltarif fare. |
| `get_departures` | Upcoming departures from a stop.              |

### Waymarked Trails (`mcp_waymarkedtrails_*`)

Call in this order:

1. `search_routes_in_region(region, activity="cycling")` — find marked routes near the tour area.
2. `get_route_details(route_id)` — retrieve length, markings, and operator.
3. `get_route_segments(route_id)` — get stages and towns along the route.

For hiking options use `activity="hiking"`. Apply rating thresholds from `user-preferences.md` (≥4.0 stars, ≥30 reviews).

## Routing

Use `mcp_brouter_calculate_route` with **`profile=safety`** as default.

The `safety` profile prioritizes designated cycle paths, shared-use paths, and quiet residential streets. It avoids roads without cycling infrastructure (Landstraßen ohne Radweg).

- **3–6 waypoints** total (including start and end)
- **Round trips**: first and last waypoint MUST have identical coordinates
- Start/end near train stations with S-Bahn/Regionalbahn access
- Waypoints form a logical loop — no backtracking
- Place waypoints on **through-roads or intersections**, never dead-end streets (BRouter snaps to the nearest road segment; a cul-de-sac creates a spur)

### Detour Check

After calculating with `safety`, recalculate the same waypoints with `trekking` and compare distances.

If `safety` adds **more than 20% extra distance**:

1. Add a note in the tour description: `ℹ️ Die sichere Route ist {X} km länger als die kürzeste Strecke, da sie Landstraßen ohne Radweg meidet.`
2. Identify which segment causes the detour and explain why (e.g., no parallel cycle path available).
3. Offer the `trekking` GPX as an alternative download for cyclists comfortable with road traffic.

### Spur Removal (Post-Processing)

After saving a GPX, scan for spurs caused by dead-end snapping:

- **Detection**: `point[i] ≈ point[j]` (distance < 15 m) with `j > i + 4`
- **Fix**: Remove points `i+1` through `j-1`, re-save the GPX, and update the distance in the tour markdown.

### Regional Cycling Routes Reference

Use when selecting waypoints and writing segment descriptions.

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

## Points of Interest

POI priorities and interest order are defined in `user-preferences.md`. Map marker categories map to emojis as follows:

| Emoji | Overpass categories                                |
| ----- | -------------------------------------------------- |
| 🏛️    | museum, castle, memorial, ruins, church, viewpoint |
| 🎨    | artwork, gallery                                   |
| 🍺    | beer_garden, cafe, restaurant                      |
| 🏊    | swimming                                           |

Pass Overpass category names directly to the `render_gpx_map` `pois` parameter.

### POI Curation for Map Rendering

- Select ~15–25 POIs for the map.
- Prioritize by interest order from `user-preferences.md`.
- Deduplicate within a 200 m radius (see `user-preferences.md`).

### POI Formatting in Tour Text

```markdown
- {emoji} **[{Name}]({official-URL})** — {Description}. (~{X} €/P., {opening hours})
```

- Link to the official website or tourism page. Never use Google Maps or TripAdvisor.
- Entry price: `(~{X} €/P.)` when applicable.
- Opening hours inline, e.g. `(Di–So, Mo geschlossen)`.
- Prefix required advance booking with `⚠️ vorab buchen`.
- Priority order: Wandern → Baden → Küche → Gärten → Kunst.

### Hiking Routes

```markdown
- 🥾 **{Name}** — {Distanz}, {Dauer}, {Schwierigkeit}. ⭐ {Rating} ({N} Reviews). {Description}. [Waymarked Trails]({URL})
  - 🍺 **Einkehr:** {Restaurant/Bar} — {Beschreibung}.
```

- Rating sourced from AllTrails/Komoot via web search. Prefer ≥4.0 stars, ≥30 reviews.
- One-way routes: flag with `⚠️ One-way` and describe the return transport.
- Swimming at the endpoint: note inline with 🏊.

### Swimming / Bathing

```markdown
- 🏊 **{Name}** — {Type: See/Fluss/Freibad/Felstöpfe}. {Brief description}.
```

- Search the **entire route** for swimming spots, not just the endpoint.
- Include river pools, lakes, and outdoor pools — not just beaches.

## Weather

Every tour MUST include: temperature range, precipitation probability, wind speed and direction.

Warn explicitly if:

- Rain probability > 50%
- Storms are forecast
- Temperature > 35 °C or < 0 °C

If the forecast is unfavorable, suggest alternative dates or time windows.

## Public Transit

- **Default departure**: ~09:00 ab Blankenfelde
- 1–2 transfers acceptable
- Every tour MUST include the following note:
  > 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).

### Transit Verification Steps

1. Resolve stop IDs via `search_stops`.
2. Query connections via `get_journeys`.
3. Present only API-verified information.
4. If the API is unavailable: add `ℹ️ Verbindungen nicht per API verifiziert.` and omit line/time claims.

### Disruption Check (Schienenersatzverkehr)

Before finalizing transit, check for active disruptions on all lines used:

1. `remote_web_search`: `S-Bahn Berlin Störungen Schienenersatzverkehr` and specific lines.
2. `remote_web_search`: `"S-Bahn Berlin Bauarbeiten Störungen {tour date month/year}"`.
3. Fetch `https://sbahn.berlin/en/plan-a-journey/timetable-changes/` for replacement services.

**If SEV (Schienenersatzverkehr) is active on any segment:**

- Note the affected segment and duration in the Nahverkehrsanbindung section.
- Add:
  > ⚠️ **Schienenersatzverkehr:** {Linie} zwischen {A} und {B} bis {Datum}. Ersatzbusse fahren — zusätzliche Reisezeit einplanen.
- Add:
  > 🚲⚠️ In Ersatzbussen ist die Fahrradmitnahme in der Regel nicht möglich. Alternative Verbindung ohne SEV-Abschnitt prüfen.
- Suggest an alternative connection that avoids the SEV segment.
- If no bike-friendly alternative exists, suggest an alternative date.

**If no disruptions found**: no warning needed.

## Events

- Search via `remote_web_search` for events along the route on the tour date.
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local event calendars.
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Chorin Musiksommer).
- Always include this section — add a note if no events were found.

## File Structure

All tour files live under `trips/bike/`:

```
trips/bike/
├── README.md                          # Tour catalog index
└── {tour-name}/
    ├── index.md                       # Tour description
    ├── gpx/{tour-name}.gpx            # GPX track
    └── img/
        ├── {tour-name}.png            # Route map image
        └── {tour-name}-elevation.png  # Elevation profile image
```

- Naming: descriptive kebab-case, no `-runde` suffix. Example: `spreewald/index.md`.
- Paths inside tour markdown are **relative**: `gpx/spreewald.gpx`, `img/spreewald.png`.
- Output format: follow `bike-template.md` exactly.

## Tour Catalog Index (`trips/bike/README.md`)

Table columns: Tour (linked, theme emoji prefix), Distanz, Fahrzeit, Region. Ends with bike-transport note.

When adding a tour, **append** a row to the existing table. Do not rewrite the file.

## Workflow

Execute phases in order. Do not skip or reorder steps.

### Phase 1: Route Generation

1. **Geocode** waypoints via `search_location`. Verify each coordinate falls within the bounding box.
2. **Calculate route** via `calculate_route` using `profile=safety` (3–6 waypoints; first = last for round trips).
3. **Save GPX** to `trips/bike/{name}/gpx/{name}.gpx`.
4. **Check for spurs** in the saved GPX. Remove and re-save if detected.

### Phase 2: Enrichment

5. **Search POIs** via `search_pois_along_route` with presets `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst` — **one call at a time, sequentially**.
6. **Render map** via `render_gpx_map` with ~15–25 curated, deduplicated POI markers. Save to `trips/bike/{name}/img/{name}.png`.
7. **Render elevation profile** via `render_elevation_profile`. Save to `trips/bike/{name}/img/{name}-elevation.png`.
8. **Hiking options** — `search_routes_in_region` + web search for ratings. Apply thresholds from `user-preferences.md`.
9. **Swimming** — web search for lakes, rivers, and outdoor pools along the entire route.
10. **Practical info** — verify opening days, booking requirements, and seasonal closures for every major POI via web search.
11. **Query weather** for the tour date using start-location coordinates.
12. **Verify transit** from/to S Blankenfelde (TF) Bhf via VBB tools.
13. **Check disruptions** as described in the Disruption Check section.
14. **Search events** via `remote_web_search`.

### Phase 3: Output

15. **Write tour markdown** to `trips/bike/{name}/index.md` following `bike-template.md` exactly.
16. **Update index** — append a row to `trips/bike/README.md`.
17. **Present summary** to the user in German.

## Error Handling

| Failure                     | Action                                                                  |
| --------------------------- | ----------------------------------------------------------------------- |
| Geocode returns no results  | Retry with a more specific name. If still failing, ask the user.        |
| Route calculation fails     | Check waypoint order and coordinates. Adjust intermediate waypoints.    |
| VBB API unavailable         | Add `ℹ️ Verbindungen nicht per API verifiziert.` Omit line/time claims. |
| Overpass returns no results | Note the absence in the section. Do not fabricate POIs.                 |
| Weather API unavailable     | Add `ℹ️ Wetterdaten nicht verfügbar.`                                   |

## Tour Lifecycle (Refreshing Existing Tours)

GPX tracks and map images are stable and do not need to be regenerated. Only refresh date-dependent sections:

| Section              | Tool                | Reason                                |
| -------------------- | ------------------- | ------------------------------------- |
| Wetter               | `weather_forecast`  | Forecasts change daily                |
| Veranstaltungen      | `remote_web_search` | Events are seasonal                   |
| Nahverkehrsanbindung | `get_journeys`      | Schedules change per timetable period |

After refreshing, update the `ℹ️ Zuletzt geprüft: {date}` timestamp. If a section cannot be verified, write `ℹ️ Nicht verifiziert.`
