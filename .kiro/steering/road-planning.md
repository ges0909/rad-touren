---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Planning — Europe

Plan, generate, and present multi-day car rental road trips across Europe.

## Language Rules

- User-facing output (trip markdown, descriptions, summaries, chat): **German**
- Code, file names, tool calls: **English/kebab-case**

## Geographic Scope

- Destinations: Anywhere in Europe reachable by direct or one-stop flight from BER
- Origin: Berlin Brandenburg Airport (BER)
- All trips form a loop returning to the departure airport city unless a direct return flight from the endpoint is confirmed

## Critical Conventions (Never Violate)

1. **No fabrication**: Never invent restaurants, hotels, hike names, travel times, or prices. Only present information from web search or API results. If data is unavailable, state that explicitly.
2. **Coordinate order**: All MCP tool calls use **[longitude, latitude]** — longitude first. Swapping produces routes in the wrong location.
3. **Verify distances**: Calculate the full route via `mcp_osrm_calculate_car_route` with all waypoints in order. This gives accurate driving times for coastal and mountain roads (which can be 1.5–2× longer than straight-line distance). Flag any segment exceeding 4 hours.
   - **Scenic routes with intermediate stops**: When a driving day includes planned detours or waypoints (e.g., coastal road via villages), calculate the **total distance through all waypoints**, not just start → end. Sum the individual legs. The table must show the scenic-route distance, not the direct highway distance.
4. **Seasonal awareness**: Check weather and seasonal closures (mountain passes, ferry schedules, swimming season). Flag off-season risks.
5. **Overpass rate limit**: Query POI presets **sequentially** (one at a time). Never parallelize Overpass requests.
6. **Buffer rule**: When the trip starts and ends in the same city, place the **longer stay (2+ nights) at the end** as a buffer for the return flight. First night at the departure city: 1 night max (arrival only).
7. **Source attribution**: When information comes from web search, note the check date: `ℹ️ Zuletzt geprüft: {date}`.
8. **Map–table sync**: Every stop mentioned in the day's text MUST appear as a labeled marker on the route map. Use `scripts/render_roadtrip_map.py` with `--stations` for ALL stops (including swim spots, detours). Use combined labels when POIs are close (e.g., "Urdaibai / Playa de Laga"). When the itinerary changes, re-render affected maps.

## Trip Profile

- **Travel group**: 2 persons (see `user-preferences.md`)
- **Transport**: Compact rental car, pickup/dropoff near airport
- **Duration per stop**: 1–3 nights
- **Stops**: 4–8 stops forming a logical loop
- **Max single drive**: 4 hours. If exceeded, suggest a break stop or split the segment.
- **Train segments**: Allowed as alternative between stops where scenic or practical
- **Cycling day trips**: Can replace hiking if bike rental is available. Search for rental options and suggest routes.
- **Detours between stops**: Suggest brief detours (max 30–60 min extra) to notable sights, viewpoints, or villages along the way. Present as optional "Unterwegs" tips.

## Interests & POI Rules

All interests, emoji mappings, food/drink rules, and accommodation rules are defined in `user-preferences.md`. Key "always" items for roadtrips:

- 🎨 Moderne Kunst — **always highlight**
- 🌿 Botanische Gärten — **always include when nearby**

Do NOT use 🍇 (Weingüter) or ☕ (Kaffee) as separate categories — these were removed from preferences. Wine/coffee can be mentioned under 🍷 (Regionale Küche) when relevant to local culture.

Use `remote_web_search` to find POIs matching these interests at each stop. Prioritize by the interest priority order in `user-preferences.md`.

## Allowed MCP Servers

Use **only** these MCP servers for roadtrip planning. Do **not** use VBB (Berlin-only transit) or BRouter (cycling-specific).

| Server          | Prefix                   | Purpose                                               |
| --------------- | ------------------------ | ----------------------------------------------------- |
| ors             | `mcp_openrouteservice_*` | Geocoding, driving times, isochrones, distance matrix |
| osrm            | `mcp_osrm_*`             | Car routing with GPX export (full street geometry)    |
| overpass        | `mcp_overpass_*`         | POI search along routes (requires GPX file)           |
| open-meteo      | `mcp_open_meteo_*`       | Weather forecast for destinations                     |
| wikivoyage      | `mcp_wikivoyage_*`       | Travel guide content for destinations                 |
| waymarkedtrails | `mcp_waymarkedtrails_*`  | Discover marked hiking/cycling routes                 |

**Tool selection for routing:**

- **Route with map display** (ALWAYS use for the final route): `mcp_osrm_calculate_car_route` — pass ALL waypoints in order. This is the ONLY tool that shows the route on the map.
- **Geocoding** (place → coordinates): `mcp_openrouteservice_geocode`
- **GPX export** (for file download): `mcp_osrm_route_to_gpx`

Do NOT use `mcp_openrouteservice_driving_time` — use `mcp_osrm_calculate_car_route` instead, which provides both distance/duration AND map display.

## MCP Tool Reference

### Routing & Geocoding (`mcp_openrouteservice_*`)

| Tool              | Key Parameters & Notes                                                                          |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| `geocode`         | Place name → coordinates. Optional `country` filter (ISO 3166-1 alpha-2). Returns `[lon, lat]`. |
| `driving_time`    | Quick point-to-point: `from_coords` and `to_coords` as `[lon, lat]`. Returns km and duration.   |
| `distance_matrix` | N×N matrix for multiple locations. Compare route order options.                                 |
| `isochrone`       | Reachability areas from a point. Validate "what's within X minutes" of a stop.                  |

### Car Routing & GPX Export (`mcp_osrm_*`)

| Tool                  | Key Parameters & Notes                                                                                            |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `calculate_car_route` | `waypoints`: list of `[lon, lat]` pairs. Returns distance, duration, per-leg breakdown. No API key needed.        |
| `route_to_gpx`        | `waypoints` + `output_path` + optional `station_names`. Saves full street geometry as GPX. Use for map rendering. |

### POIs (`mcp_overpass_*`)

| Tool                      | Key Parameters & Notes                                                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `search_pois_along_route` | Requires **absolute GPX path**. Presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. Query **sequentially**. |

Use only when a GPX track exists for a segment. For general stop-based POI discovery, prefer `remote_web_search`.

### Weather (`mcp_open_meteo_*`)

| Tool               | Key Parameters & Notes                                                                       |
| ------------------ | -------------------------------------------------------------------------------------------- |
| `weather_forecast` | `latitude`, `longitude`. Use `daily` for temperature/precipitation. Specify `forecast_days`. |
| `geocoding`        | Resolve place names to coordinates for weather queries.                                      |

### Travel Guides (`mcp_wikivoyage_*`)

| Tool                   | Key Parameters & Notes                                                                                        |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| `search_destinations`  | Find articles by destination name. Use `lang="de"` for German content.                                        |
| `get_article_sections` | List available sections before fetching. Avoids fetching irrelevant content.                                  |
| `get_section`          | Fetch specific sections: `Küche`, `Sehenswürdigkeiten`, `Aktivitäten`, `Anreise`. Targeted over full article. |
| `search_nearby`        | Find destinations near coordinates. Useful for discovering lesser-known stops along the route.                |

### Hiking & Cycling Routes (`mcp_waymarkedtrails_*`)

| Tool                      | Key Parameters & Notes                                                                  |
| ------------------------- | --------------------------------------------------------------------------------------- |
| `search_routes`           | Search by region/keyword. Set `activity="hiking"` or `"cycling"`.                       |
| `search_routes_in_region` | Search by region name. Good for discovering routes near a stop.                         |
| `get_route_details`       | Length, markings, operator, website. Use route_id from search results.                  |
| `get_route_segments`      | Stages and towns along the way. Helps describe multi-day routes or select day sections. |

## Workflow

Execute in order when the user requests a new roadtrip:

### Phase 1: Route Design

1. **Check travel advisories**: Search `remote_web_search` for `"Auswärtiges Amt Reisehinweise {country}"`. If a full travel warning is active, inform the user and ask whether to proceed. If partial warning, note prominently in the trip document.
2. **Determine airports**: Search for flights from BER to destination region via `remote_web_search`. Identify arrival/departure airport. Apply flight preferences from `user-preferences.md` (direct flights preferred, time windows, day preferences).
3. **Research established itineraries**: Search `remote_web_search` for packaged round trips (e.g., `"Rundreise {region}" Reiseveranstalter`, `"{region} road trip itinerary"`). Extract route patterns from 3–5 sources as inspiration.
4. **Validate route geometry**: If researched routes suggest a linear (A→B) trip, check whether a direct return flight exists from the endpoint to BER. If **no direct flight** exists, **prefer a circular route** returning to the departure airport city.
5. **Design itinerary**: Plan 4–8 stops forming a logical loop. Incorporate interesting stops from step 3 where they fit the trip profile and interests.
6. **Geocode stops**: Resolve all stop names to coordinates via `geocode` (with `country` filter).
7. **Calculate driving times**: Use `driving_time` for **each consecutive segment**. Flag segments > 4 hours and suggest break stops.
8. **Validate**: Ensure total trip fits requested duration. Apply buffer rule for same-city start/end.

### Phase 2: Enrichment (per stop)

For each stop, gather information in this order:

9. **Travel guide context**: Query `mcp_wikivoyage_*` — use `get_article_sections` first, then `get_section` for relevant sections (Küche, Sehenswürdigkeiten, Aktivitäten). This provides baseline knowledge for the stop.
10. **Accommodation**: Search via `remote_web_search`. Apply accommodation rules from `user-preferences.md` (small/boutique, central, 80–150 €/night).
11. **Hiking**: Search `mcp_waymarkedtrails_*` for marked routes near each stop (`search_routes` or `search_routes_in_region`). Get details for promising routes. Supplement with `remote_web_search` for unmarked local trails.
    - **Every day should have a hiking option** — if no major hike fits, add a short walk (2–3 Std.)
    - **GPX downloads**: Include Waymarked Trails GPX link for all routes with a route ID
    - **One-way routes**: Flag and provide public transport info (bus line + timetable link)
    - **Einkehr**: Search for refreshment options (bars, restaurants, huts) at start, endpoint, or midpoint of each hike
12. **Swimming**: Search for beaches, lakes, thermal baths, river pools, and rock pools via `remote_web_search`.
    - **Driving days**: Always check for swimming stops along the route (not just at destination)
    - **Hiking days**: Check if trail ends at or passes a swimming spot
    - Include thermal springs, river bathing, Felstöpfe — not just sea beaches
13. **Food & Drink**: Search for regional restaurants, markets, local specialties. Apply food rules from `user-preferences.md`.
14. **Culture & Art**: Search for galleries, museums, historic sites. Prioritize modern/contemporary art (highest interest priority).
15. **Practical info**: For every major POI (museums, caves, gardens, guided tours), verify via `remote_web_search`:
    - **Opening days** — note weekly closures (e.g., "Di+Mi geschlossen")
    - **Advance booking** — flag if tickets must be purchased in advance (e.g., "⚠️ vorab buchen")
    - **Seasonal closures** — flag if the POI is closed during the travel period
    - Cross-check that planned activities fall on valid opening days in the day-by-day table.
16. **Weather**: Query `weather_forecast` for each stop's coordinates and travel dates.

### Phase 3: Output

17. **Write trip markdown** to `trips/road/{name}.md` following the template below.
18. **Update index** — append a row to `trips/road/README.md`. Do **not** rewrite the file.
19. **Present summary** to user in German.

## File Structure

```
trips/road/
├── README.md              # Trip catalog index
├── {trip-name}.md         # Trip description
├── gpx/                   # GPX tracks
│   ├── {start}-{ziel}.gpx    # Car routes per driving day (start-destination naming)
│   └── {trip-name}.gpx       # Full trip route (optional)
└── img/
    └── {start}-{ziel}.png    # Route maps per driving day (matching GPX names)
```

- Naming: descriptive kebab-case, ASCII-safe (no umlauts: ü→ue, ö→oe, ä→ae, ß→ss)
- GPX/IMG files: named by start-destination (e.g., `bilbao-san-sebastian.gpx`)
- Trip files: named by region (e.g., `nordspanien-kueste.md`)

## Output Template

See `road-template.md` for the full markdown template structure.

## Map Rendering

Generate route maps for each driving day:

```bash
# 1. Create GPX with street geometry — include ALL stops (swim, detours)
mcp_osrm_route_to_gpx(waypoints=[...], output_path="trips/road/gpx/{start}-{ziel}.gpx", station_names=[...])

# 2. Render map — every text stop must be a labeled station
python scripts/render_roadtrip_map.py trips/road/gpx/{start}-{ziel}.gpx trips/road/img/{start}-{ziel}.png \
  --stations '{Name}:{lon},{lat}' ...
```

Rules:

- One map per driving day (not one for the whole trip)
- Station labels = stop names from the text (combined when close: "Urdaibai / Playa de Laga")
- Include Google Maps direction link below each map for route verification
- File naming: `{start}-{ziel}` in kebab-case (e.g., `bilbao-san-sebastian.png`)

## Trip Catalog Index (`trips/road/README.md`)

Table with columns: Trip (linked), Dauer, Region, Schwerpunkt.
When adding a trip, **append** a row. Do **not** rewrite the file.

## Error Handling

| Failure                 | Action                                                              |
| ----------------------- | ------------------------------------------------------------------- |
| No flight info found    | Note flight time, suggest Skyscanner. Mark: `ℹ️ Nicht verifiziert.` |
| No hiking trails found  | Search alternative terms. If empty, note absence.                   |
| Weather API unavailable | `ℹ️ Wetterdaten nicht verfügbar.`                                   |
| Driving time unclear    | Estimate ~80 km/h rural, ~120 km/h highway. Mark: `ℹ️ Geschätzt.`   |
| Hotel search empty      | Suggest booking.com/Airbnb with criteria.                           |
| Geocode fails           | Retry with country filter. If still failing, ask user.              |
| Wikivoyage no article   | Use `remote_web_search` instead.                                    |

## Trip Lifecycle (Refreshing)

| Section     | Tool                | Reason                 |
| ----------- | ------------------- | ---------------------- |
| Wetter      | `weather_forecast`  | Forecasts change daily |
| Flüge       | `remote_web_search` | Prices change          |
| Unterkünfte | `remote_web_search` | Availability changes   |

Update `ℹ️ Zuletzt geprüft: {date}` timestamp when refreshing.
