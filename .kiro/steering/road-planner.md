---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Planner — Europe

Workflow for planning multi-day car rental road trips across Europe. See `road-output-template.md` for document formatting, `user-preferences.md` for universal rules, and `road-preferences.md` for roadtrip-specific preferences (flights, accommodation, food, interests).

## Language

User-facing output: **German**. Code, file names, GPX metadata: **English/kebab-case**.

## Trip Profile

- Origin: BER
- Group: 2 persons, compact rental (airport pickup/dropoff)
- Duration: 1–3 nights per stop, 4–8 stops forming a logical loop
- Return: loop back to departure airport unless a direct return flight from the endpoint is confirmed

## Hard Rules

Never violate these:

1. **Coordinate order** — All MCP tool calls use `[longitude, latitude]`. Swapping breaks routing.
2. **Route verification** — Calculate every segment via `mcp_osrm_calculate_car_route`. Flag segments > 4 hours. Never estimate without calling the tool.
3. **Overpass rate limit** — Query POI presets sequentially, never in parallel.
4. **Buffer rule** — Same-city start/end: first stop = 1 night max; longer stay (2+ nights) goes at the end as a flight buffer.
5. **Map–text sync** — Every stop named in the day's text MUST appear as a labeled marker on the route map. Re-render when the itinerary changes.

## Driving Constraints

- Max single drive: 4 hours. If exceeded, add a break stop or split the day.
- Train segments: allowed where scenic or practical.
- Detours: suggest 30–60 min optional stops ("Unterwegs") to notable sights between cities.

## Allowed MCP Servers

Do NOT use VBB (Berlin-only transit) or BRouter (cycling-specific).

| Server          | Prefix                   | Purpose                                         |
| --------------- | ------------------------ | ----------------------------------------------- |
| ors             | `mcp_openrouteservice_*` | Geocoding, driving times, isochrones, matrix    |
| osrm            | `mcp_osrm_*`             | Car routing + GPX export (full street geometry) |
| overpass        | `mcp_overpass_*`         | POI search along GPX routes (OSM)               |
| open-meteo      | `mcp_open_meteo_*`       | Weather forecast                                |
| wikivoyage      | `mcp_wikivoyage_*`       | Travel guide content                            |
| waymarkedtrails | `mcp_waymarkedtrails_*`  | Marked cycling routes                           |
| serpapi-flights | `mcp_serpapi_flights_*`  | Google Flights — live prices and schedules      |
| podcasts        | `mcp_podcasts_*`         | Travel podcast search + transcript extraction   |

### Tool Selection

| Intent                          | Tool                                   | Notes                                                     |
| ------------------------------- | -------------------------------------- | --------------------------------------------------------- |
| Route with map display (ALWAYS) | `mcp_osrm_calculate_car_route`         | Pass ALL waypoints including detour stops.                |
| Geocoding (place → coords)      | `mcp_openrouteservice_geocode`         | Always use `country` filter for accuracy.                 |
| GPX export                      | `mcp_osrm_route_to_gpx`                | Required for map rendering and Overpass queries.          |
| Compare route orderings         | `mcp_openrouteservice_distance_matrix` | N×N matrix for multiple stop orderings.                   |
| Reachability check              | `mcp_openrouteservice_isochrone`       | "What's reachable within X minutes" of a stop.            |
| Flight search                   | `mcp_serpapi_flights_search_flights`   | BER as origin. Apply flight preferences from preferences. |

Do NOT use `mcp_openrouteservice_driving_time` — `mcp_osrm_calculate_car_route` provides distance, duration, AND map display in one call.

### Wikivoyage Pattern

1. `get_article_sections` — discover available sections first
2. `get_section` — fetch targeted sections: `Küche`, `Sehenswürdigkeiten`, `Aktivitäten`, `Anreise`
3. `search_nearby` — discover lesser-known stops along the route

Always use `lang="de"`.

### Overpass Pattern

Requires an absolute GPX path. Available presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. **Query sequentially — never in parallel.** For stop-based POI discovery without a GPX, use `remote_web_search`.

Note: Do NOT use 🍇 (Weingüter) or ☕ (Kaffee) as standalone POI categories — mention them under 🍷 when relevant to local food culture.

### Waymarked Trails Pattern

Use `search_routes_in_region` to discover marked cycling routes near stops. See `user-preferences.md` for the full tool sequence and rating thresholds.

### Podcast Pattern (optional enrichment)

Use to surface hidden stops, authentic restaurant tips, and seasonal warnings:

1. `search_podcast_episodes(query)` — find episodes about the destination or region
2. `get_podcast_episodes(feed_id)` — browse episodes; look for 📝 transcript availability
3. `get_episode_transcript(transcript_url)` — extract spoken content for route tips

Best used during Phase 1 research alongside written itinerary sources.

## Workflow

### Phase 1: Route Design

1. **Travel advisory** — Search `"Auswärtiges Amt Reisehinweise {country}"`. Full warning → inform user and pause. Partial → note prominently in the output.
2. **Flights** — `mcp_serpapi_flights_search_flights` (BER origin). Apply flight preferences from `user-preferences.md`. Note prices and schedules for outbound and return.
3. **Research itineraries** — Search `"Rundreise {region}"` and `"{region} road trip itinerary"`. Extract patterns from 3–5 sources. Search podcasts for local insights not found in written guides.
4. **Route shape** — Linear A→B trip: verify a direct return flight exists. No direct flight → prefer a circular route.
5. **Design stops** — 4–8 stops, logical loop, incorporating researched highlights.
6. **Geocode** — Resolve all stop names via `mcp_openrouteservice_geocode` (with `country` filter).
7. **Drive times** — `mcp_osrm_calculate_car_route` for each consecutive segment. Flag any segment > 4 hours.
8. **Validate** — Total duration fits the requested days. Apply buffer rule.

### Phase 2: Enrichment (per stop)

9. **Travel guide** — Wikivoyage: sections `Küche`, `Sehenswürdigkeiten`, `Aktivitäten`.
10. **Accommodation** — Web search. Apply rules from `road-preferences.md`.
11. **Wandern (day hikes)** — Web search for hiking trails:
    - Every day should have a hiking option (2–5 h, moderate difficulty)
    - Use AllTrails, Komoot, Wikiloc for trail discovery and ratings (≥4.0 stars, ≥30 reviews)
    - Note trailhead access, parking, and return logistics
    - Flag difficulty level and gear requirements
    - Identify Einkehr options at start/endpoint
12. **Swimming** — Web search for beaches, lakes, thermal baths, river pools, rock pools. Check driving-day routes for en-route swimming stops.
13. **Food & Drink** — Apply rules from `user-preferences.md`. Note markets and local specialties.
14. **Culture & Art** — Prioritize modern/contemporary art per interest table.
15. **Practical verification** — For every major POI, confirm via web search:
    - Opening days (note weekly closures)
    - Advance booking requirements (`⚠️ vorab buchen`)
    - Seasonal closures during the travel period
16. **Weather** — `mcp_open_meteo_weather_forecast` for each stop's coordinates.

### Phase 3: Output

17. **Write trip markdown** — `trips/road/{name}/index.md` following `road-output-template.md`.
18. **Update catalog** — Append a row to `trips/road/README.md`. Do NOT rewrite the file.
19. **Present summary** — German, to user.

## File Structure

```
trips/road/
├── README.md                    # Trip catalog (append-only)
└── {trip-name}/
    ├── index.md                 # Trip description (German)
    ├── review.md                # Optional cross-LLM review
    ├── gpx/
    │   └── {start}-{ziel}.gpx  # Car route per driving day
    └── img/
        └── {start}-{ziel}.png  # Route map per driving day
```

Naming: kebab-case, ASCII-safe (ü→ue, ö→oe, ä→ae, ß→ss). GPX and image files named by start–destination segment.

## Map Rendering

One map per driving day. Steps:

```bash
# 1. Export GPX with all waypoints (including detour/swim stops)
mcp_osrm_route_to_gpx(waypoints=[[lon,lat], ...], output_path="trips/road/{trip}/gpx/{start}-{ziel}.gpx", station_names=[...])

# 2. Render with labeled stations and POIs
python scripts/render_roadtrip_map.py trips/road/{trip}/gpx/{start}-{ziel}.gpx trips/road/{trip}/img/{start}-{ziel}.png \
  --stations 'T{N} {Name}:{lon},{lat}' ... \
  --pois 'category:name:lon,lat' ...
```

Valid POI categories: `art`, `hike`, `swim`, `food`, `wine`, `sight`, `nature`, `coffee`.

Station labels: use day-prefixed names like `T1 Bilbao`. Combine labels when POIs are close (e.g., `Urdaibai / Playa de Laga`). Include a Google Maps direction link below each map for verification.

## Trip Catalog Index

`trips/road/README.md` — columns: Trip (linked), Dauer, Region, Schwerpunkt. Always **append**, never rewrite.

## Error Handling

| Failure                 | Action                                                                                                            |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| No flight info found    | Retry with `search_airport` then `search_flights`. Still empty → suggest Skyscanner. Mark `ℹ️ Nicht verifiziert.` |
| No hiking trails found  | Try alternative search terms. Note absence if still empty.                                                        |
| Weather API unavailable | `ℹ️ Wetterdaten nicht verfügbar.`                                                                                 |
| Driving time unclear    | Estimate ~80 km/h rural, ~120 km/h highway. Mark `ℹ️ Geschätzt.`                                                  |
| Hotel search empty      | Suggest booking.com/Airbnb with criteria from `user-preferences.md`.                                              |
| Geocode fails           | Retry with `country` filter. Still failing → ask user.                                                            |
| Wikivoyage no article   | Fall back to `remote_web_search`.                                                                                 |

## Refreshing Existing Trips

| Section     | Tool                    | Reason                 |
| ----------- | ----------------------- | ---------------------- |
| Wetter      | `mcp_open_meteo_*`      | Forecasts change daily |
| Flüge       | `mcp_serpapi_flights_*` | Prices change          |
| Unterkünfte | `remote_web_search`     | Availability changes   |

Update `ℹ️ Zuletzt geprüft: {date}` when refreshing any section.
