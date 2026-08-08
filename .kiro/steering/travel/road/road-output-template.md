---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Output Template

Format specification for roadtrip markdown files in `trips/road/`. Each file is a self-contained multi-day itinerary combining driving routes, activities, and maps.

This document defines the **output structure only**. For workflow, tool usage, and research process, see `road-planner.md`. For user preferences (interests, food, accommodation), see `road-preferences.md`.

## File & Naming Conventions

```
trips/road/{trip-name}/
├── index.md                           # Trip document (German)
├── gpx/{start}-{ziel}.gpx            # Car route per driving day
└── maps/tag-{NN}-{start}-{ziel}.png  # Route map per driving day
```

### Naming Rules

- **Folder names:** kebab-case, ASCII-safe (ü→ue, ö→oe, ä→ae, ß→ss)
- **GPX files:** `{start}-{ziel}.gpx` — segment-based naming (e.g., `bilbao-bakio.gpx`)
- **Map files:** `tag-{NN}-{start}-{ziel}.png` — day-prefixed with zero-padded number (e.g., `tag-01-bilbao-bakio.png`, `tag-14-vitoria-rioja-vitoria.png`)
- **Image folder:** Always `maps/` (not `img/`) for consistency across all trip types
- All file names use lowercase ASCII characters only

## Document Structure

Trip files start with empty YAML front matter (`---\n---\n`). Major sections separated by `---` horizontal rules.

**Required sections in order:**

1. Title + Compact Header (inkl. Route overview)
2. Übernachtungen im Überblick
3. Vorab-Reservierungen _(only if advance booking needed)_
4. Tagesplan (day-by-day itinerary)
5. Quellen

Omit optional sections entirely if empty — never leave blank headings.

---

## Section 1: Title + Compact Header

```markdown
# {Destination} Roadtrip

**Reisezeitraum:** {Wochentag} {Datum von} – {Wochentag} {Datum bis} · {N} Tage · ~{X} km (inkl. Tagesausflüge)
**Flug:** BER ↔ {Airport}, Direktflug {Airline} (nur {Flugtage}, {Tageszeit})
**Mietwagen:** Übernahme {Datum} ({Ort}) / Abgabe {Datum} ({Ort}) — {N} Tage

**Reiseverlauf:** [{Stop 1}](#anchor) → [{Stop 2}](#anchor) → ... → [{Stop N}](#anchor). {Fahrzeit-Zusammenfassung}.

🌊 {One-line trip highlight}

☀️ **Wetter:** {Temperaturbereich}, Regen {X}%. {Saisonaler Hinweis}.

🇪🇸 **Länderinfo:** {Preisniveau}. Tempolimit: {X} / {Y} / {Z} km/h. {Besonderheiten}. Notruf {N}. {Lokale Bräuche}.

📱 **Nützliche Apps & Ausrüstung:** {App-Empfehlungen}. {Packliste-Tipps}.

💡 **Flexibilität:** {Wetter-Alternativen, Museumsbackup bei Regen}.
```

**Rules:**

- All meta-info lives in these header paragraphs — do NOT create separate chapters for Wetter, Anreise, Kostenübersicht, or Tipps. Use plain paragraphs with emoji prefix (not blockquotes).
- Always include weekday abbreviations in Reisezeitraum.
- Flight times appear inline at Tag 1 (Hinflug) and last day (Rückflug), never in the header.
- Country flag emoji matches destination country (🇪🇸, 🇮🇹, 🇫🇮, etc.).
- Apps & gear paragraph: include only when the trip has special requirements (tides, mountain gear, transit cards). Omit for generic trips.
- Reiseverlauf: list all major stops linked to their day heading anchors, separated by `→`. End with a driving-time summary sentence.

---

## Section 3: Übernachtungen im Überblick

Structural skeleton showing where the traveller sleeps each night. The "Unterkunft" column stays empty — the user fills it after booking.

```markdown
| Datum             | Nächte | Ort                                          | Unterkunft |
| ----------------- | ------ | -------------------------------------------- | ---------- |
| Fr 4. – Sa 5. Sep | 1      | [Bakio](#tag-1--fr-4-sep--bilbao--bakio-...) |            |
| Sa 5. – Mo 7. Sep | 2      | [San Sebastián](#tag-3--so-6-sep--san-...)   |            |
```

**Rules:**

- One row per accommodation stop (not per night).
- Date range format: `{Wochentag} {Tag}. – {Wochentag} {Tag}. {Monat}` (German abbreviations).
- "Ort" column: link each location to its first relevant day heading using a markdown anchor (`[Ort](#tag-n--...)`). The anchor is derived from the `###` day heading (lowercase, spaces → hyphens, special chars removed).
- "Unterkunft" column: filled manually by the user after booking. Never overwrite, delete, or suggest changes to existing entries. Leave empty cells empty — the AI must not insert hotel recommendations.
- End with footer: `**Gesamt:** {N} Nächte ({Start-Datum}–{End-Datum})`

---

## Section 4: Vorab-Reservierungen

Include only when attractions require or strongly recommend advance booking. Omit section entirely otherwise.

```markdown
| Tag / Datum           | Aktivität / Ort              | Vorlauf    | Details & Buchungs-Link                                     | ✅  |
| :-------------------- | :--------------------------- | :--------- | :---------------------------------------------------------- | :-- |
| **Tag 2** (Sa 5. Sep) | **San Juan de Gaztelugatxe** | 2–4 Wochen | Kostenloses Zeitslot-Ticket. [visitbiscay.eus](https://...) | [ ] |
```

**Rules:**

- Left-align all columns.
- Include recommended lead time (e.g., "2–4 Wochen").
- Sort chronologically by trip day.
- "✅" column: checkboxes (`[ ]`) for the user to manually mark completed bookings. Never modify existing checkbox states — user-managed content is read-only for the AI.
- Optional tip below table: `💡 **Tipp:** {advice}`

---

## Section 2: Tagesplan

One `###` heading per day. All days use the same heading level (`###`).

### Day Heading Formats

| Day Type | Format                                                                   |
| -------- | ------------------------------------------------------------------------ |
| Driving  | `### Tag {N} · {Wochentag} {Datum} · {Von} → {Ziel} · {X} km, ~{Y} Std.` |
| Stay     | `### Tag {N} · {Wochentag} {Datum} · {Ort}`                              |
| Day trip | `### Tag {N} · {Wochentag} {Datum} · {Ziel} (Tagesausflug, {X} Min.)`    |

### Day Content Order (chronological)

1. **Route map block** _(driving days only — immediately after heading)_
2. **Flight info** _(arrival/departure days only)_
3. **Fahrt / Unterwegs-Stopps** _(morning driving)_
4. **Aktivitäten am Zielort** _(afternoon/evening)_
5. **Kulinarisches** _(food neighborhoods + regional specialties, NOT specific restaurants)_

**Special day patterns:**

- Arrival day: Flug → Transfer → Kulinarisches Viertel
- Departure day: Aktivitäten → Fahrt zum Flughafen → Rückflug

### Route Map Block

Required for every driving day. Place immediately after the day heading. Maps are wrapped in a collapsible `<details>` toggle for a cleaner overview:

```markdown
<details>
<summary>🗺️ Karte anzeigen</summary>

![Tag {N}: {Von} → {Ziel}](maps/tag-{NN}-{von}-{ziel}.png)

[📍 Google Maps](https://www.google.com/maps/dir/{Von}/{Stopp1}/{Stopp2}/{Ziel})

</details>
```

**Rules:**

- Use `<details><summary>🗺️ Karte anzeigen</summary>` to wrap maps (collapsed by default).
- Empty line required after `<summary>` and before `</details>`.
- Google Maps link uses 📍 pin emoji: `[📍 Google Maps](url)`.
- Map file naming: `tag-{NN}-{von}-{ziel}.png` where `{NN}` is zero-padded day number (01, 02, ..., 14, 15).

### Route Variants

Use when alternative routes exist (timing, weather, or optional stops):

```markdown
**Empfohlene Route (Variante A):**

1. POI 1 (~7:30 Uhr)
2. POI 2 (~9:00 Uhr)

**Alternative mit {Bedingung} (Variante B):**

1. POI 2 (~9:00 Uhr)
2. POI 1 (~13:00 Uhr)
```

---

## POI Formatting

### Emoji Legend

| Emoji | Category                                 |
| ----- | ---------------------------------------- |
| 🥾    | Wandern                                  |
| 🏊    | Baden (Strand, Fluss, Therme, Felstöpfe) |
| 🍷    | Essen & Trinken                          |
| 🎨    | Kunst & Museen                           |
| 🏛️    | Sehenswürdigkeiten                       |
| ☕    | Kaffee                                   |

**POI priority order within a day:** Wandern → Baden → Küche → Gärten → Kunst.

### Standard POI Format

```markdown
- {emoji} **[{Name}]({official-URL})** [📍]({Google Maps link}) — {Description}. (~{X} €/P., {opening hours})
```

**Rules:**

- Name link → official website or tourism page. Never Google Maps, TripAdvisor, or temporary URLs.
- 📍 pin → Google Maps coordinate link (`https://www.google.com/maps/search/?api=1&query={lat},{lon}`). Include for POIs requiring driving or non-obvious locations. Omit for central city attractions.
- Entry price: `(~{X} €/P.)` when applicable.
- Opening hours inline: e.g., `(Di–So, Mo geschlossen)`.
- Advance booking: prefix with `⚠️ Tickets vorab online buchen` or `⚠️ Reservierung empfohlen`.

### Hiking Route Format

```markdown
- 🥾 **{Name}** — {Distanz}, {Dauer}, {Schwierigkeit}. ⭐ {Rating} ({N} Reviews). {Description}. [Waymarked Trails]({URL}) · [GPX ↓]({download-URL})
```

**Rules:**

- Link to Waymarked Trails (`https://hiking.waymarkedtrails.org/#route?id={id}`). Fallback: AllTrails or Komoot.
- Rating: include when available (prefer ≥4.0 stars). Source: AllTrails, Komoot, or Wikiloc.
- Flag one-way routes: `⚠️ One-way` + describe return transport.
- Note swimming at endpoint inline with 🏊.
- Every day should offer at least one hiking option (minimum: short walk 2–3 Std.).
- Multiple options: present as numbered list with pros/cons.

### Culinary Format

Do NOT recommend specific restaurants. Instead, provide orientation:

```markdown
- 🍷 **{Viertel/Straße}** — {Description: type of food scene, what's typical here}. **Probieren:** {regional specialty 1}, {specialty 2}.
```

**Examples:**

```markdown
- 🍷 **Parte Vieja** (San Sebastián) — Pintxos-Gassen mit dutzenden Bars auf engem Raum. **Probieren:** Gilda (Sardelle, Peperoni, Olive), Txakoli.
- 🍷 **Calle Gascona** (Oviedo) — „Bulevar de la Sidra", komplette Straße voller Sidrerías. **Probieren:** Sidra escanciar, Fabada Asturiana, Cachopo.
```

**Exception — reservation mechanics:** When a place has a specific booking mechanism the user must know (not a normal reservation), include it:

```markdown
- 🍷 **Bar Nestor** (San Sebastián) — Berühmt für Tortilla. ⚠️ Keine Reservierung möglich. Persönlich auf Liste eintragen: 12:00 Uhr (mittags) oder 19:00 Uhr (abends).
```

### Swimming Format

```markdown
- 🏊 **{Name}** [📍]({Google Maps link}) — {Type: Strand/Fluss/Therme/Felstöpfe}. {Brief description}.
```

- Include swimming options for driving days (en-route stops).
- Cover variety: river pools, thermal springs, rock pools — not just beaches.

---

## Section 5: Quellen

### Hiking Routes Table

```markdown
| Route  | Länge  | Link                         | GPX            |
| ------ | ------ | ---------------------------- | -------------- |
| {Name} | {X} km | [waymarkedtrails.org]({URL}) | [↓]({GPX-URL}) |
```

### Travel Guides & Inspiration

```markdown
Routen-Inspiration (recherchiert {Monat} {Jahr}):

- [{Source Name} — {Title}]({URL}) — {Brief description}

Reiseführer (Wikivoyage, CC BY-SA 3.0):
[{Destination 1}]({URL}) · [{Destination 2}]({URL})
```

### Video & Podcast Sources (optional)

```markdown
Sehempfehlungen zur Vorbereitung (ÖR Mediathek):

| Sender | Titel                                            | Link                    |
| ------ | ------------------------------------------------ | ----------------------- |
| WDR    | Wunderschön! — {Title} (45 Min., UT, bis {Jahr}) | [ARD Mediathek]({URL})  |
| BR     | Podcast: Radioreisen — {Title} (54 Min.)         | [Apple Podcasts]({URL}) |
```

**Rules:**

- Include duration and availability window (e.g., "bis 2029") for Mediathek content.
- Prefer official broadcaster sources (BR, WDR, NDR) over commercial platforms.
- Always end Quellen section with: `ℹ️ Zuletzt geprüft: {Datum}`
- **Update the date** whenever you make substantive changes to the trip (GPX recalculation, route corrections, POI updates, map regeneration). Format changes (toggles, emoji) don't require a date update.

---

## Map Generation

Generate one map per driving day.

**Step 1 — GPX export** (all waypoints including detour/swim stops):

```python
mcp_osrm_route_to_gpx(
    waypoints=[[lon, lat], ...],
    output_path="trips/road/{trip-name}/gpx/{start}-{ziel}.gpx",
    station_names=[...]
)
```

**Step 2 — Render map image** with labeled stations and POI markers:

```bash
python scripts/render_roadtrip_map.py \
  trips/road/{trip-name}/gpx/{start}-{ziel}.gpx \
  trips/road/{trip-name}/maps/tag-{NN}-{start}-{ziel}.png \
  --stations 'T{N} {Name}:{lon},{lat}' ... \
  --pois 'category:name:lon,lat' ...
```

**File naming:**

- GPX: `{start}-{ziel}.gpx` (segment-based)
- Map: `tag-{NN}-{start}-{ziel}.png` (day-prefixed with zero-padded number)

**render_roadtrip_map.py parameters:**

| Parameter    | Format                    | Description                                                                               |
| ------------ | ------------------------- | ----------------------------------------------------------------------------------------- |
| `--stations` | `'T{N} Name:lon,lat'`     | Major stops as labeled circle markers (day-prefixed)                                      |
| `--pois`     | `'category:name:lon,lat'` | POI icons. Categories: `art`, `hike`, `swim`, `food`, `wine`, `sight`, `nature`, `coffee` |
| `--width`    | integer                   | Image width in px (default: 900)                                                          |
| `--height`   | integer                   | Image height in px (default: 600)                                                         |

**Map–text sync rule:** Every stop mentioned in the day's text MUST appear as a station or POI marker on the map. No stop without a marker. Combine labels when POIs are close (e.g., "Urdaibai / Playa de Laga"). Re-render maps whenever itinerary changes.

---

## Language & Formatting Rules

| Concern        | Rule                                                                     |
| -------------- | ------------------------------------------------------------------------ |
| Language       | All trip content in **German** (weekdays, dates, descriptions)           |
| Date formats   | `{Wochentag} {Tag}. {Monat}` (e.g., "Fr 4. Sep") or `TT.MM.YYYY`         |
| Code artifacts | English, kebab-case (file names, GPX metadata)                           |
| Separators     | `---` horizontal rules separate major sections only — never within a day |
| Whitespace     | No trailing whitespace, no empty sections, no blank headings             |
| Links          | Official websites only. Never Google Maps/TripAdvisor for POI name links |
| Verification   | Append `ℹ️ Zuletzt geprüft: {Datum}` for web-sourced data                |
| Unverifiable   | Mark with `ℹ️ Nicht verifiziert.` — never invent details                 |
