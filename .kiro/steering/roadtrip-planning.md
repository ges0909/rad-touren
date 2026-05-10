---
inclusion: fileMatch
fileMatchPattern: "roadtrips/**"
---

# Roadtrip Planning — Europe

Plan, generate, and present multi-day car rental road trips across Europe.

## Language Rules

- User-facing output (trip markdown, descriptions, summaries, chat): **German**
- Code, file names, tool calls: **English/kebab-case**

## Geographic Scope

- Destinations: Anywhere in Europe reachable by direct or one-stop flight from BER
- Origin: Berlin Brandenburg Airport (BER)
- All trips form a loop returning to the departure airport city

## Critical Conventions (Never Violate)

1. **No fabrication**: Never invent restaurants, hotels, hike names, travel times, or prices. Only present information from web search or API results.
2. **Coordinate order**: All MCP tool calls use **[longitude, latitude]** — longitude first.
3. **Verify distances**: Always calculate driving times between stops. Flag if a single segment exceeds 4 hours.
4. **Seasonal awareness**: Check weather and seasonal closures (mountain passes, ferry schedules, swimming season).
5. **Overpass rate limit**: Query POI presets **sequentially** (one at a time). Never parallelize Overpass requests.
6. **Buffer rule**: When the trip starts and ends in the same city, place the **longer stay (2+ nights) at the end** as a buffer for the return flight. First night(s) at the departure city: 1 night max (arrival/jet lag only).

## Trip Profile

- **Travel group**: 2 persons (see `user-preferences.md`)
- **Transport**: Compact rental car, pickup/dropoff near airport
- **Duration per stop**: 1–3 nights
- **Stops**: 4–8 stops forming a logical loop
- **Max single drive**: 4 hours. If exceeded, suggest a break stop or split the segment.
- **Train segments**: Allowed as alternative between stops where scenic or practical
- **Cycling day trips**: Can replace hiking if bike rental is available. Search for rental options and suggest routes.
- **Interests**: See `user-preferences.md` for full priority list. Key "always" items:
  - 🎨 Moderne Kunst — **always highlight**
  - 🌿 Botanische Gärten — **always include when nearby**
  - ☕ Kaffeeröstereien — **always mention when found**
  - 🍇 Weingüter — **always include in wine regions**
  - 🪖 Kalter Krieg — **always highlight**

## Allowed MCP Servers

Use **only** these MCP servers for roadtrip planning. Do **not** use VBB (Berlin-only transit).

| Server     | Prefix                   | Purpose                                         |
| ---------- | ------------------------ | ----------------------------------------------- |
| ors        | `mcp_openrouteservice_*` | Car/bike/foot routing, geocoding, driving times |
| overpass   | `mcp_overpass_*`         | POI search along routes or near stops           |
| open-meteo | `mcp_open_meteo_*`       | Weather forecast for destinations               |

Flights, rental cars, and hotels: use `remote_web_search`.

### MCP Tool Reference

#### Routing & Geocoding (`mcp_openrouteservice_*`)

| Tool              | Key Parameters & Notes                                                                                                           |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `geocode`         | Place name → coordinates. Optional `country` filter (ISO 3166-1 alpha-2). Returns `[lon, lat]`.                                  |
| `calculate_route` | `coordinates`: list of `[lon, lat]` pairs (min 2, max 50). `profile`: `driving-car` (default), `foot-hiking`, `cycling-regular`. |
| `driving_time`    | Quick point-to-point: `from_coords` and `to_coords` as `[lon, lat]`. Returns distance (km) and duration.                         |

#### POIs (`mcp_overpass_*`)

| Tool                      | Key Parameters & Notes                                                                                                                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `search_pois_along_route` | Requires **absolute GPX path**. Presets: `einkehr`, `badestellen`, `sehenswuerdigkeiten`, `kunst`, `radservice`, `rast`. Query **sequentially**. |

#### Weather (`mcp_open_meteo_*`)

| Tool               | Key Parameters & Notes                                                                       |
| ------------------ | -------------------------------------------------------------------------------------------- |
| `weather_forecast` | `latitude`, `longitude`. Use `daily` for temperature/precipitation. Specify `forecast_days`. |
| `geocoding`        | Resolve place names to coordinates for weather queries.                                      |

## Workflow

Execute in order when the user requests a new roadtrip:

### Phase 1: Route Design

1. **Check travel advisories**: Search `remote_web_search` for `"Auswärtiges Amt Reisehinweise {country}"`. If warnings exist (partial travel warning, travel warning), note them prominently at the top of the trip document. If a full travel warning is active, inform the user and ask whether to proceed.
2. **Determine airports**: Search for flights from BER to destination region via `remote_web_search`. Identify arrival/departure airport.
3. **Design itinerary**: Plan 4–8 stops forming a logical loop back to the departure airport.
4. **Geocode stops**: Resolve all stop names to coordinates via `geocode` (with `country` filter).
5. **Calculate driving times**: Use `driving_time` for each segment. Flag segments > 4 hours.
6. **Validate**: Ensure total trip fits requested duration. Apply buffer rule for same-city start/end.

### Phase 2: Enrichment (per stop)

6. **Accommodation**: Search via `remote_web_search`. Apply rules from `user-preferences.md` (small/boutique, central, 80–150 €/night).
7. **Hiking**: Search for day hikes near each stop (moderate, 3–5 hours). Use local-language terms if needed (sentiero, randonnée, polku).
8. **Swimming**: Search for beaches, lakes, or thermal baths.
9. **Food & Drink**: Search for regional restaurants, markets, local specialties. Apply food rules from `user-preferences.md`.
10. **Culture & Art**: Search for galleries, museums, historic sites. Prioritize modern/contemporary art.
11. **Weather**: Query `weather_forecast` for each stop's coordinates and travel dates.

### Phase 3: Output

12. **Write trip markdown** to `roadtrips/{name}.md` following the template below.
13. **Update index** — append row to `roadtrips/README.md`. Do not rewrite the file.
14. **Present summary** to user in German.

## File Structure

```
roadtrips/
├── README.md              # Trip catalog index
├── {trip-name}.md         # Trip description
├── gpx/{trip-name}/       # GPX tracks for hikes (optional)
└── img/{trip-name}/       # Route maps, photos (optional)
```

- Naming: descriptive kebab-case. Example: `sardinien-ostkueste.md`, `provence-lavendel.md`
- Use ASCII-safe characters in file names (no umlauts: ü→ue, ö→oe, ä→ae)

## Trip Markdown Template

Every trip file MUST start with empty YAML front matter (`---\n---\n`) and contain these sections in order, separated by `---` horizontal rules.

### 1. Title

```markdown
# {Destination} Roadtrip ({N} Tage)
```

### 2. Metadata Block

```markdown
**Reisezeitraum:** {Datum von} – {Datum bis}
**Dauer:** {N} Tage / {N-1} Nächte
**Stationen:** {N} Stopps
**Gesamtstrecke:** ~{X} km
**Flug:** BER → {Airport} (Hin) / {Airport} → BER (Rück)
**Mietwagen:** Übernahme/Abgabe {Airport}
```

Followed by a tip box:

```markdown
> {emoji} **Tipp:** {one-line highlight of the trip}
```

Emoji by theme: 🏛️ culture, 🌿 nature, 🌸 seasonal, 🌊 water/coast, 🌲 forest, 🍂 autumn, ☀️ summer.

### 3. Routenübersicht

```markdown
## Routenübersicht

{Airport/Stadt 1} → {Stopp 2} → {Stopp 3} → … → {Airport/Stadt 1}

| #   | Station | Nächte | Fahrzeit ab vorheriger |
| --- | ------- | ------ | ---------------------- |
| 1   | {Ort}   | {N}    | — (Ankunft)            |
| 2   | {Ort}   | {N}    | ~{X} Std. ({Y} km)     |
| …   | …       | …      | …                      |
```

Add warnings below the table for notable conditions:

- `> ⚠️ **Längste Etappe:** {A} → {B} ({X} km, ~{Y} Std.). Pause in {C} empfohlen.`
- `> 💡 **Puffer-Regel:** {explanation}`

### 4. Stationen (one H2 per stop)

```markdown
## {N}. {Ortsname} ({N} Nächte)

{Kurzbeschreibung des Ortes und warum er auf der Route liegt.}

**Unterkunft:** {Name} — {kurze Beschreibung, Preisniveau}
```

Each stop includes relevant subsections (omit if no data found):

```markdown
### Wandern

- 🥾 **{Name}** — {Distanz}, {Dauer}, {Schwierigkeit}. {Kurzbeschreibung.}

### Baden

- 🏊 **{Name}** — {Beschreibung}

### Essen & Trinken

- 🍷 **{Restaurant/Markt}** — {Spezialität, Preisniveau}
- ☕ **{Rösterei/Café}** — {Beschreibung}

### Kultur

- 🎨 **{Galerie/Museum}** — {Kurzbeschreibung}
- 🏛️ **{Historische Stätte}** — {Kurzbeschreibung}
- 🪖 **{Cold War Site}** — {Kurzbeschreibung}
```

POI subsection rules:

- Only include subsections with actual verified data
- Use emoji from `user-preferences.md` interest table consistently
- Deduplicate POIs that appear in multiple sources
- Prioritize by interest priority order (art first, then hiking, swimming, food, etc.)

### 5. Wetter

```markdown
## Wetter

> ℹ️ _Zuletzt geprüft: {date}. Vor der Reise aktuelles Wetter prüfen._

| Station | Temperatur    | Regen | Besonderheiten |
| ------- | ------------- | ----- | -------------- |
| {Ort}   | {min}–{max}°C | {X}%  | {ggf. Hinweis} |
```

Add packing/weather warnings below the table when relevant (heat, rain, storms, cold nights).

### 6. Anreise & Mietwagen

```markdown
## Anreise & Mietwagen

**Hinflug:** BER → {Airport}, ~{X} Std. {Airlines mit Direktflügen.}
**Rückflug:** {Airport} → BER, ~{X} Std.

- Geschätzte Flugkosten: ~{X}–{Y} € pro Person (Roundtrip)
- Frühbucher-Tipp: 2–3 Monate vorher buchen

**Mietwagen:**

- Übernahme: {Airport}, {Datum}
- Abgabe: {Airport}, {Datum}
- Empfehlung: Kompaktwagen (reicht für 2 Personen + Gepäck)
- Geschätzte Kosten: ~{X}–{Y} € für {N} Tage (Vollkasko inkl.)

> 💡 Mietwagen frühzeitig buchen. Vergleichsportale: CHECK24, billiger-mietwagen.de
```

### 7. Kostenübersicht

```markdown
## Kostenübersicht (Schätzung, 2 Personen)

| Posten                   | Geschätzt      |
| ------------------------ | -------------- |
| Flüge (2×)               | ~{X}–{Y} €     |
| Mietwagen ({N} Tage)     | ~{X}–{Y} €     |
| Unterkünfte ({N} Nächte) | ~{X}–{Y} €     |
| Benzin (~{X} km)         | ~{X}–{Y} €     |
| Essen & Aktivitäten      | ~{X}–{Y} €     |
| **Gesamt**               | **~{X}–{Y} €** |
```

Use ranges (min–max) rather than single values for cost estimates.

### 8. Packliste & Tipps

Optional section with trip-specific packing tips, driving notes, or local customs. Include when the destination has notable differences from Germany.

### 9. Länderinfo

Every roadtrip MUST include this section:

```markdown
## Länderinfo

|                           |                                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Preisniveau**           | {günstiger / ähnlich / teurer} als Deutschland                                                                                       |
| **Tempolimit Landstraße** | {X} km/h                                                                                                                             |
| **Tempolimit Autobahn**   | {X} km/h                                                                                                                             |
| **Tempolimit innerorts**  | {X} km/h                                                                                                                             |
| **Besonderheiten**        | {Maut, Lichtpflicht, Winterreifen, etc.}                                                                                             |
| **Reisehinweise**         | {Keine Einschränkungen / Teilreisewarnung / Reisewarnung} ([Auswärtiges Amt](https://www.auswaertiges-amt.de/de/ReiseUndSicherheit)) |
```

If a travel advisory exists, add a warning box above the table:

```markdown
> ⚠️ **Reisehinweis Auswärtiges Amt:** {Zusammenfassung der Warnung}. Aktuelle Infos: [auswaertiges-amt.de](https://www.auswaertiges-amt.de/de/ReiseUndSicherheit/{country-path})
```

### 10. Erweiterungsideen (optional)

If the destination region has natural extensions (e.g., a northern/southern variant, a longer version), add a brief note with route sketch and best season.

## Trip Catalog Index (`roadtrips/README.md`)

Table with columns: Trip (linked), Dauer, Region, Schwerpunkt.

When adding a trip, **append** a row to the existing table. Do not rewrite the file.

## Error Handling

| Failure                 | Action                                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------------------- |
| No flight info found    | Note approximate flight time, suggest checking Skyscanner/Google Flights                             |
| No hiking trails found  | Search with alternative terms (Wanderweg, sentiero, randonnée, polku). If still empty, note absence. |
| Weather API unavailable | Add `ℹ️ Wetterdaten nicht verfügbar.`                                                                |
| Driving time unclear    | Estimate: ~80 km/h rural roads, ~120 km/h highways. Mark as estimate.                                |
| Hotel search empty      | Suggest booking platforms (booking.com, Airbnb) with search criteria                                 |

## Trip Lifecycle (Refreshing Existing Trips)

Trips are inspiration templates. Date-dependent sections need refreshing:

| Section     | Tool                | Reason                         |
| ----------- | ------------------- | ------------------------------ |
| Wetter      | `weather_forecast`  | Forecasts change daily         |
| Flüge       | `remote_web_search` | Prices and availability change |
| Unterkünfte | `remote_web_search` | Availability changes           |

When refreshing, update the `ℹ️ Zuletzt geprüft: {date}` timestamp. If unverifiable: `ℹ️ Nicht verifiziert.`
