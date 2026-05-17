---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Planning — Europe

Plan, generate, and present multi-day car rental road trips across Europe.

## Language

Defer to `user-preferences.md`. Summary: user-facing output in **German**, code/filenames in **English/kebab-case**.

## Scope & Trip Profile

- Origin: BER (flight preferences in `user-preferences.md`)
- Group: per `user-preferences.md` (2 persons, compact rental)
- Duration per stop: 1–3 nights, 4–8 stops forming a logical loop
- All trips return to the departure airport city unless a direct return flight from the endpoint is confirmed

## Hard Rules (Never Violate)

Content integrity rules (no fabrication, source attribution, seasonal awareness) are defined in `user-preferences.md` and apply here. Additional roadtrip-specific rules:

1. **Coordinate order** — All MCP tool calls use `[longitude, latitude]`. Swapping breaks routing.
2. **Verify distances** — Calculate full routes via `mcp_osrm_calculate_car_route` with all waypoints. Scenic routes with intermediate stops: sum individual legs. Flag segments > 4 hours.
3. **Overpass rate limit** — Query POI presets sequentially, never in parallel.
4. **Buffer rule** — Same-city start/end: place the longer stay (2+ nights) at the end as flight buffer. First night: 1 night max.
5. **Map–table sync** — Every stop in the day's text MUST appear as a labeled marker on the route map. Re-render maps when itinerary changes.

## Driving & Route Constraints

- Max single drive: 4 hours. If exceeded, suggest a break stop or split.
- Train segments: allowed where scenic or practical.
- Cycling day trips: allowed if bike rental is available.
- Detours between stops: suggest brief detours (30–60 min extra) to notable sights. Present as optional "Unterwegs" tips.

## Interest Priorities (Roadtrip-Specific)

Defer to `user-preferences.md` for the full interest table and priority order. Roadtrip-specific additions:

- Do NOT use 🍇 (Weingüter) or ☕ (Kaffee) as separate categories — mention under 🍷 when relevant to local culture.
- Use `remote_web_search` to find POIs at each stop (Overpass only when GPX exists).

## Allowed MCP Servers

Do NOT use VBB (Berlin-only transit) or BRouter (cycling-specific).

| Server          | Prefix                   | Purpose                                            |
| --------------- | ------------------------ | -------------------------------------------------- |
| ors             | `mcp_openrouteservice_*` | Geocoding, driving times, isochrones, matrix       |
| osrm            | `mcp_osrm_*`             | Car routing with GPX export (full street geometry) |
| overpass        | `mcp_overpass_*`         | POI search along routes (requires GPX)             |
| open-meteo      | `mcp_open_meteo_*`       | Weather forecast                                   |
| wikivoyage      | `mcp_wikivoyage_*`       | Travel guide content                               |
| waymarkedtrails | `mcp_waymarkedtrails_*`  | Marked hiking/cycling routes                       |

### Tool Selection for Routing

| Intent                          | Tool                                   | Notes                                   |
| ------------------------------- | -------------------------------------- | --------------------------------------- |
| Route with map display (ALWAYS) | `mcp_osrm_calculate_car_route`         | Pass ALL waypoints. Shows route on map. |
| Geocoding (place → coords)      | `mcp_openrouteservice_geocode`         | Use `country` filter for accuracy.      |
| GPX export (file download)      | `mcp_osrm_route_to_gpx`                | For map rendering and Overpass queries. |
| Compare route orders            | `mcp_openrouteservice_distance_matrix` | N×N matrix for multiple locations.      |
| Reachability check              | `mcp_openrouteservice_isochrone`       | "What's within X minutes" of a stop.    |

Do NOT use `mcp_openrouteservice_driving_time` — use `mcp_osrm_calculate_car_route` instead (provides distance, duration, AND map display).

### Overpass POI Search

Requires an absolute GPX path. Available presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. Query sequentially. For general stop-based POI discovery, prefer `remote_web_search`.

### Wikivoyage Usage Pattern

1. `get_article_sections` — discover available sections first
2. `get_section` — fetch targeted sections: `Küche`, `Sehenswürdigkeiten`, `Aktivitäten`, `Anreise`
3. `search_nearby` — discover lesser-known stops along the route

Always use `lang="de"` for German content.

### Waymarked Trails Usage Pattern

Defer to `user-preferences.md` for the general tool sequence. For roadtrips, use `search_routes_in_region` to find hikes near each stop.

## Workflow

### Phase 1: Route Design

1. **Travel advisories** — Search `"Auswärtiges Amt Reisehinweise {country}"`. Full warning → inform user. Partial → note prominently.
2. **Airports** — Search flights from BER. Apply flight preferences from `user-preferences.md`.
3. **Research itineraries** — Search for packaged round trips (`"Rundreise {region}"`, `"{region} road trip itinerary"`). Extract patterns from 3–5 sources.
4. **Validate route geometry** — Linear A→B trip: check for direct return flight. No direct flight → prefer circular route.
5. **Design itinerary** — 4–8 stops, logical loop, incorporating researched highlights.
6. **Geocode stops** — Resolve all stop names via `mcp_openrouteservice_geocode` (with `country` filter).
7. **Calculate driving times** — Use `mcp_osrm_calculate_car_route` for each consecutive segment. Flag > 4 hours.
8. **Validate** — Total trip fits requested duration. Apply buffer rule.

### Phase 2: Enrichment (per stop)

For each stop, gather in this order:

9. **Travel guide** — Wikivoyage: `get_article_sections` → `get_section` (Küche, Sehenswürdigkeiten, Aktivitäten).
10. **Accommodation** — Web search. Apply rules from `user-preferences.md`.
11. **Hiking** — Waymarked Trails + web search. Rules:
    - Every day should have a hiking option (short walk 2–3 Std. if no major hike)
    - Include GPX download link where available (Waymarked Trails route page — GPX via download icon on the website, no direct API URL)
    - Flag one-way routes + provide public transport info
    - Search for Einkehr at start, endpoint, or midpoint
12. **Swimming** — Web search for beaches, lakes, thermal baths, river pools, rock pools.
    - Driving days: check for swimming stops along the route
    - Hiking days: check if trail ends at or passes a swimming spot
13. **Food & Drink** — Apply rules from `user-preferences.md`.
14. **Culture & Art** — Prioritize modern/contemporary art per interest table.
15. **Practical info** — For every major POI, verify via web search:
    - Opening days (note weekly closures)
    - Advance booking requirements (`⚠️ vorab buchen`)
    - Seasonal closures during travel period
    - Cross-check planned activities fall on valid opening days
16. **Weather** — `mcp_open_meteo_weather_forecast` for each stop's coordinates.

### Phase 3: Output

17. **Write trip markdown** — `trips/road/{name}/index.md` following `road-template.md`.
18. **Update index** — Append a row to `trips/road/README.md`. Do NOT rewrite the file.
19. **Present summary** — German, to user.

## File Structure

```
trips/road/
├── README.md              # Trip catalog index
├── {trip-name}/
│   ├── index.md           # Trip description
│   ├── gpx/
│   │   └── {start}-{ziel}.gpx    # Car routes per driving day
│   └── img/
│       └── {start}-{ziel}.png    # Route maps per driving day
```

Naming: kebab-case, ASCII-safe (ü→ue, ö→oe, ä→ae, ß→ss). GPX/IMG named by start-destination segment.

## Map Rendering

One map per driving day. Workflow:

```bash
# 1. GPX with all waypoints (including swim/detour stops)
mcp_osrm_route_to_gpx(waypoints=[...], output_path="trips/road/{trip-name}/gpx/{start}-{ziel}.gpx", station_names=[...])

# 2. Render with labeled stations
python scripts/render_roadtrip_map.py trips/road/{trip-name}/gpx/{start}-{ziel}.gpx trips/road/{trip-name}/img/{start}-{ziel}.png \
  --stations '{Name}:{lon},{lat}' ...
```

- Station labels = stop names from text (combine when close: "Urdaibai / Playa de Laga")
- Include Google Maps direction link below each map for verification

## Trip Catalog Index

`trips/road/README.md` — Table with columns: Trip (linked), Dauer, Region, Schwerpunkt. Always append, never rewrite.

## Error Handling

| Failure                 | Action                                                           |
| ----------------------- | ---------------------------------------------------------------- |
| No flight info found    | Note gap, suggest Skyscanner. Mark `ℹ️ Nicht verifiziert.`       |
| No hiking trails found  | Try alternative search terms. Note absence if still empty.       |
| Weather API unavailable | `ℹ️ Wetterdaten nicht verfügbar.`                                |
| Driving time unclear    | Estimate ~80 km/h rural, ~120 km/h highway. Mark `ℹ️ Geschätzt.` |
| Hotel search empty      | Suggest booking.com/Airbnb with criteria.                        |
| Geocode fails           | Retry with country filter. If still failing, ask user.           |
| Wikivoyage no article   | Fall back to `remote_web_search`.                                |

## Refreshing Existing Trips

| Section     | Tool                | Reason                 |
| ----------- | ------------------- | ---------------------- |
| Wetter      | `weather_forecast`  | Forecasts change daily |
| Flüge       | `remote_web_search` | Prices change          |
| Unterkünfte | `remote_web_search` | Availability changes   |

Update `ℹ️ Zuletzt geprüft: {date}` timestamp when refreshing.
