---
inclusion: always
---

# Radtouren-Planung — Berlin/Brandenburg

Plan, generate, and present cycling day-trip tours in the Berlin/Brandenburg region.

## Language Rules

- User-facing output (tour markdown, descriptions, summaries, chat responses): **German**.
- Tool calls, code identifiers, file names, GPX `track_name` values: **English/kebab-case**.

## Geographic Scope

- Bounding box: lat 51.3–53.6, lon 11.3–14.8.
- All tours must be reachable by public transit from **S Blankenfelde (TF) Bhf**.
- After every geocode call, verify coordinates fall within bounds. Reject and re-geocode with a more specific query if outside.

## Critical Conventions

- **Coordinate order**: All MCP tool calls use **[longitude, latitude]** — longitude first. Swapping produces routes in the wrong location.
- **Absolute paths**: `mcp_brouter_render_gpx_map`, `mcp_brouter_render_elevation_profile`, and `mcp_overpass_search_pois_along_route` require **absolute file paths**. The MCP server runs from `mcp/brouter/`, so relative paths resolve incorrectly.
- **Overpass rate limit**: Query POI presets **sequentially** (one at a time). Do not parallelize Overpass requests.

## Routing Rules

Use `mcp_brouter_calculate_route` with `profile=trekking` (default).

- **3–6 waypoints** total (including start/end).
- **Round trips**: First and last waypoint MUST have identical coordinates.
- Start/end near train stations with S-Bahn/Regionalbahn access.
- Waypoints form a logical loop — no backtracking.
- Place waypoints on **through-roads or intersections**, never dead-end streets. BRouter snaps to the nearest road segment; a cul-de-sac creates a spur.

### GPX Post-Processing: Spur Removal

After saving a GPX file, check for spurs (out-and-back segments from dead-end snapping).

**Detection**: `point[i] ≈ point[j]` (distance < 15 m) with `j > i + 4`.
**Fix**: Remove points `i+1` through `j-1`, re-save GPX, update distance in tour markdown.

### Regional Cycling Routes Reference

Use these when selecting waypoints and writing segment descriptions:

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

### Routing & Maps (`mcp_brouter_*`)

- **`search_location`** — Geocode via Nominatim. Default `country_code=de`. Returns `[lon, lat]`. Rate-limited to 1 req/s (server-side).
- **`calculate_route`** — Required: `waypoints` (list of `[lon, lat]`). Optional: `profile`, `format` (`gpx`|`geojson`), `track_name`, `nogos`, `alternativeidx`. Returns distance, elevation, duration, GPX/GeoJSON. GPX includes elevation in `<trkpt>`.
- **`render_gpx_map`** — Renders GPX as PNG (800×600 default). Accepts optional `pois` list (dicts with `lat`, `lon`, `category`, `name`) for emoji markers. Legend auto-drawn when POIs present. **Absolute paths required.**
- **`render_elevation_profile`** — Renders elevation chart as PNG. Reports min/max elevation, total ascent/descent. **Absolute paths required.**

### POIs (`mcp_overpass_*`)

- **`search_pois_along_route`** — Finds POIs along GPX route. **Absolute GPX path required.** Presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. Query sequentially.

### Weather (`mcp_open_meteo_*`)

- **`weather_forecast`** — Forecast for coordinates. Use start-location coords and tour date.

### Transit (`mcp_vbb_*`)

- **`search_stops`** — Resolve stop names to IDs.
- **`get_journeys`** — Plan connections between stops. Returns fare info for Regionaltarif.
- **`get_departures`** — Upcoming departures at a stop.

## Points of Interest

Use these emoji prefixes consistently in all tour output:

| Emoji | Category             | Guidance                                                                                                                    |
| ----- | -------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 🏛️    | Sehenswürdigkeiten   | Castles, parks, historic buildings, museums, viewpoints, churches, memorials                                                |
| 🎨    | Moderne Kunst        | Galleries, sculpture parks, installations, street art, ateliers. **Always highlight — user has a special interest in art.** |
| 🍺    | Einkehrmöglichkeiten | Cafés, beer gardens, restaurants. **Prioritize cafés with selbstgebackener Kuchen.**                                        |
| 🏊    | Badestellen          | Swimming spots at lakes along the route                                                                                     |

POI marker categories for `render_gpx_map`:

| Icon | Categories                                         |
| ---- | -------------------------------------------------- |
| 🏛️   | museum, castle, memorial, ruins, church, viewpoint |
| 🎨   | artwork, gallery                                   |
| 🍺   | beer_garden, cafe, restaurant                      |
| 🏊   | swimming                                           |

Category names match Overpass output — pass POI results through directly.

## Weather Rules

- Every tour MUST include: temperature range, precipitation probability, wind speed/direction.
- Warn if: rain probability > 50%, storms forecast, temperature > 35 °C or < 0 °C.
- If unfavorable, suggest alternative dates or time windows.

## Public Transit Rules

- **Home station**: S Blankenfelde (TF) Bhf (lines: S2, RB24, RE5, RE7, RE8).
- **Default departure**: ~09:00 Uhr ab Blankenfelde. Query outbound connections starting from 08:45.
- **Default group**: 2 persons + 2 bicycles. Calculate fares and recommend cheapest option.
- 1–2 transfers acceptable.
- Every tour MUST include: `> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).`

### Transit Verification

**Never** claim line names, connections, or travel times without querying VBB API first.

1. Resolve stop IDs via `search_stops`.
2. Query connections via `get_journeys`.
3. Present only API-verified information.
4. If API unavailable: `ℹ️ Verbindungen nicht per API verifiziert.`

### Disruption Check (Schienenersatzverkehr)

Before finalizing transit, check for disruptions on **all lines and segments** used (outbound, return, transfers):

1. `remote_web_search` for `S-Bahn Berlin Störungen Schienenersatzverkehr` and specific lines used.
2. `remote_web_search` for `"S-Bahn Berlin Bauarbeiten Störungen {tour date month/year}"`.
3. Fetch `https://sbahn.berlin/en/plan-a-journey/timetable-changes/` for replacement services on relevant lines (S2, RB24, RE5, RE7, RE8, and any others used).

**If SEV active on any segment:**

- Note affected segment and duration in Nahverkehrsanbindung.
- Add: `> ⚠️ **Schienenersatzverkehr:** {Linie} zwischen {A} und {B} bis {Datum}. Ersatzbusse fahren — zusätzliche Reisezeit einplanen.`
- Add: `> 🚲⚠️ In Ersatzbussen ist die Fahrradmitnahme in der Regel nicht möglich. Alternative Verbindung ohne SEV-Abschnitt prüfen.`
- Suggest alternative connection avoiding SEV (e.g., Regionalbahn instead of S-Bahn).
- If no bike-friendly alternative exists, suggest alternative date.

**If no disruptions found**: No warning needed.

## Events

- Search via `remote_web_search` for events along the route.
- Preferred sources: visitberlin.de, potsdam.de, reiseland-brandenburg.de, local calendars.
- Mention seasonal highlights (e.g., Baumblütenfest in Werder, Chorin Musiksommer).
- If none found, include section with a note.

## File Structure

All tour files live under `routes/`:

```
routes/
├── README.md                     # Tour catalog index
├── {tour-name}.md                # Tour description
├── gpx/{tour-name}.gpx           # GPX track
├── img/{tour-name}.png           # Route map image
└── img/{tour-name}-elevation.png # Elevation profile image
```

- Naming: descriptive kebab-case, no `-runde` suffix. Example: `spreewald.md`, `spreewald.gpx`.
- Paths inside tour markdown are **relative**: `gpx/spreewald.gpx`, `img/spreewald.png`.

## Tour Markdown Template

Every tour file MUST start with an empty YAML front matter (`---\n---\n`) and contain these sections in order, separated by `---` horizontal rules. Sections 6 (Badestellen) is omitted if no swimming spots exist.

### 1. Title

```markdown
# {Tour-Name}-Runde ab {Start/Ziel}
```

### 2. Metadata Block

Bold key-value pairs, one per line:

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

Emoji by theme: 🏛️ culture, 🌿 nature, 🌸 seasonal, 🌊 water/lakes, 🌲 forest.

### 4. Streckenverlauf

```markdown
## Streckenverlauf

{Start} → {Waypoint 1} → {Waypoint 2} → … → {Start}

[![{Tour-Name} Karte](img/{name}.png)](img/{name}.png)

[![Höhenprofil](img/{name}-elevation.png)](img/{name}-elevation.png)
```

### 5. Streckenabschnitte

One H3 per segment. Include only POI types that exist along that segment:

```markdown
## Streckenabschnitte

### {N}. {Von} → {Nach} (ca. {X} km)

{Description with path/street names in **bold**. Mention named cycling routes.}

🏛️ **{Name}** — {short description}
🎨 **{Name}** — {short description}
🍺 {Café/restaurant name} — {short description}
🏊 **{Name}** — {short description}
```

### 6. Badestellen (optional — omit if none)

```markdown
## Badestellen

- 🏊 **{Name}** — {description}
```

### 7. Einkehrmöglichkeiten

Summary of all food/drink stops from the segments.

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

Add warnings below the table for notable conditions (heat, rain, wind).

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

**Tarif (2 Personen + 2 Fahrräder):**

| Option                                     | Preis        |
| ------------------------------------------ | ------------ |
| 2× Einzelfahrt + 2× Fahrradkarte (pro Weg) | {X},XX €     |
| 2× Tageskarte + 2× Fahrradkarte            | {X},XX €     |
| Kleingruppen-Tageskarte (bis 5 Pers.)      | {X},XX €     |
| **Empfehlung: {günstigste Option}**        | **{X},XX €** |

> 🚲 Fahrradmitnahme in S-Bahn und Regionalbahn ist im VBB möglich (Fahrradkarte erforderlich).
```

### Fare Calculation Rules

- `get_journeys` returns Regionaltarif fares automatically (distance-based, use as-is).
- For Berlin ABC fares, use the reference table below.
- Always calculate for **2 persons + 2 bicycles**.
- Einzelfahrt is per direction (Hin+Rück = 2×); Tageskarte covers both ways.
- Determine tariff zone: stations like Strausberg, Eberswalde, Königs Wusterhausen use Regionaltarif (API prices). Berlin-area stations use ABC tariff (table below).

### VBB Fare Reference (Berlin ABC)

> _Last updated: 2026-05-02. Source: vbb.de, sbahn.berlin. Verify at [vbb.de/en/tickets](https://www.vbb.de/en/tickets/) if older than 6 months._

Since 01.01.2026, Berlin BC tariff area no longer exists. No 4-Fahrten-Karte for ABC.

**Personentickets:**

| Ticket                              | Regeltarif | Ermäßigt |
| ----------------------------------- | ---------- | -------- |
| Einzelfahrt Berlin AB               | 4,00 €     | 2,90 €   |
| Einzelfahrt Berlin ABC              | 5,00 €     | 3,30 €   |
| 24-Stunden-Karte Berlin AB          | 11,20 €    | 7,40 €   |
| 24-Stunden-Karte Berlin ABC         | 12,90 €    | 8,00 €   |
| Kleingruppen-Tageskarte AB (≤5 P.)  | 35,30 €    | —        |
| Kleingruppen-Tageskarte ABC (≤5 P.) | 37,70 €    | —        |
| Tageskarte VBB-Gesamtnetz           | 28,50 €    | —        |

**Fahrradtickets:**

| Ticket                              | Preis  |
| ----------------------------------- | ------ |
| Fahrrad-Einzelfahrt Berlin AB       | 2,70 € |
| Fahrrad-Einzelfahrt Berlin ABC      | 3,30 € |
| Fahrrad-Tageskarte Berlin AB (24h)  | 5,90 € |
| Fahrrad-Tageskarte Berlin ABC (24h) | 6,80 € |
| Fahrrad-Tageskarte VBB-Gesamtnetz   | 7,50 € |

## Tour Catalog Index (`routes/README.md`)

Table with columns: Tour (linked, theme emoji prefix), Distanz, Fahrzeit, Region. Ends with bike-transport note.

When adding a tour, **append** a row to the existing table. Do not rewrite the file.

## Workflow

Execute in order when the user requests a new tour:

### Phase 1: Route Generation

1. **Geocode** waypoints via `mcp_brouter_search_location`. Verify coordinates within bounds.
2. **Calculate route** via `mcp_brouter_calculate_route` (3–6 waypoints, first = last for round trips).
3. **Save GPX** to `routes/gpx/{name}.gpx`.
4. **Remove spurs** from GPX (see Spur Removal). Re-save if found.

### Phase 2: Enrichment

5. **Search POIs** via `mcp_overpass_search_pois_along_route` with presets `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst` — **sequentially**.
6. **Render map** via `mcp_brouter_render_gpx_map` with curated POI markers (~15–25, deduplicated). Save to `routes/img/{name}.png`.
7. **Render elevation** via `mcp_brouter_render_elevation_profile`. Save to `routes/img/{name}-elevation.png`.
8. **Query weather** for tour date at start-location coordinates.
9. **Verify transit** from/to S Blankenfelde (TF) Bhf via VBB tools.
10. **Check disruptions** (see Disruption Check section).
11. **Search events** via `remote_web_search`.

### Phase 3: Output

12. **Write tour markdown** to `routes/{name}.md` following the template.
13. **Update index** — append row to `routes/README.md`.
14. **Present summary** to user in German.

### Error Handling

| Failure                    | Action                                                                  |
| -------------------------- | ----------------------------------------------------------------------- |
| Geocode returns no results | Retry with more specific name. If still failing, ask user.              |
| Route calculation fails    | Check waypoint order/coordinates. Adjust intermediate waypoints.        |
| VBB API unavailable        | Add `ℹ️ Verbindungen nicht per API verifiziert.` Skip line/time claims. |
| POI search empty           | Note absence in section. Do not fabricate POIs.                         |
| Weather API unavailable    | Add `ℹ️ Wetterdaten nicht verfügbar.`                                   |

## Tour Lifecycle

Tours are templates. GPX tracks and map images are stable, but date-dependent sections need refreshing:

| Section              | Tool                              | Reason                                |
| -------------------- | --------------------------------- | ------------------------------------- |
| Wetter               | `mcp_open_meteo_weather_forecast` | Forecasts change daily                |
| Veranstaltungen      | `remote_web_search`               | Events are seasonal                   |
| Nahverkehrsanbindung | `mcp_vbb_get_journeys`            | Schedules change per timetable period |

When refreshing, update the `ℹ️ Zuletzt geprüft: {date}` timestamp. If unverifiable: `ℹ️ Nicht verifiziert.`
