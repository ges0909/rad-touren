---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Document Template

Guide for generating and editing roadtrip markdown files in `trips/road/`. Each file is a self-contained multi-day itinerary combining driving routes, accommodations, activities, and maps.

## File Structure

- Location: `trips/road/{trip-name}/index.md`
- GPX files: `trips/road/{trip-name}/gpx/{start}-{ziel}.gpx`
- Map images: `trips/road/{trip-name}/img/{start}-{ziel}.png`
- Naming: kebab-case, ASCII-safe (no umlauts, no spaces)

## Document Skeleton

Every trip file starts with empty YAML front matter (`---\n---\n`). Sections are separated by `---` horizontal rules.

Mandatory sections in order:

1. Title + Compact Header
2. Reiseverlauf (day-by-day itinerary)
3. Erweiterungsideen (optional)
4. Quellen

## Section 1: Title + Compact Header

```markdown
# {Destination} Roadtrip

**Reisezeitraum:** {Wochentag} {Datum von} – {Wochentag} {Datum bis} · {N} Tage · ~{X} km (inkl. Tagesausflüge)
**Flug:** BER ↔ {Airport}, Direktflug {Airline} (nur {Flugtage}, {Tageszeit})
**Mietwagen:** Übernahme {Datum} ({Ort}) / Abgabe {Datum} ({Ort}) — {N} Tage

> 🌊 {One-line trip highlight}

> ☀️ **Wetter:** {Temperaturbereich}, Regen {X}%. {Saisonaler Hinweis}.

> 🇪🇸 **Länderinfo:** {Preisniveau}. Tempolimit: {X} / {Y} / {Z} km/h. {Besonderheiten}. Notruf {N}. {Lokale Bräuche}.
```

Rules:

- Do NOT create separate chapters for Wetter, Anreise, Kostenübersicht, or Tipps — all meta-info lives in the header blockquotes.
- Include weekdays in Reisezeitraum.
- Flight times go inline at Tag 1 (Hinflug) and last day (Rückflug), not in the header.

## Section 2: Reiseverlauf

One `###` heading per day. All days at the same heading level.

### Day Heading Formats

Driving day:

```markdown
### Tag {N} · {Wochentag} {Datum} · {Von} → {Ziel} · {X} km, ~{Y} Std.
```

Stay day (no driving):

```markdown
### Tag {N} · {Wochentag} {Datum} · {Ort}
```

Day trip:

```markdown
### Tag {N} · {Wochentag} {Datum} · {Ziel} (Tagesausflug, {X} Min.)
```

### Chronological Order Within Each Day

List items in the order they happen:

1. Fahrt / Unterwegs-Stopps (morning)
2. **Unterkunft** (after arrival)
3. Aktivitäten am Zielort (afternoon/evening)

Arrival day: Flug → Transfer → Unterkunft → Abendessen
Departure day: Aktivitäten → Fahrt zum Flughafen → Rückflug

### Route Map Block (driving days only)

Every driving day gets a map image and a Google Maps link immediately after the heading:

```markdown
![Tag {N}: {Von} → {Ziel}](img/{von}-{ziel}.png)
[Route in Google Maps](https://www.google.com/maps/dir/{Von}/{Stopp1}/{Stopp2}/{Ziel})
```

### Accommodation Format

```markdown
**Unterkunft:** [{Name}]({booking.com-URL}) ({Rating}, ~{N} Reviews) — {Beschreibung} (~{X}–{Y} €/Nacht)
```

- Always link directly to the booking.com hotel page.
- Place chronologically after arrival, before evening activities.

## POI Formatting

```markdown
- {emoji} **[{Name}]({description-URL})** [📍](https://www.google.com/maps/search/?api=1&query={lat},{lon}) — {Description}. (~{X} €/P., {opening hours})
```

Rules:

- Description link → official website or tourism page.
- 📍 pin → Google Maps coordinate link. Only add for POIs requiring driving (not walkable from accommodation).
- Entry price: `(~{X} €/P.)` when applicable.
- Opening hours: inline, e.g. `(Di–So, Mo geschlossen)`.
- Advance booking: prefix with `⚠️ Tickets vorab online buchen`.
- Priority order: Wandern → Baden → Küche → Gärten → Kunst.

### Emoji Legend

| Emoji | Category                                 |
| ----- | ---------------------------------------- |
| 🥾    | Wandern                                  |
| 🏊    | Baden (Strand, Fluss, Therme, Felstöpfe) |
| 🍷    | Essen & Trinken                          |
| 🎨    | Kunst & Museen                           |
| 🏛️    | Sehenswürdigkeiten                       |
| ☕    | Kaffee                                   |

## Hiking Routes

```markdown
- 🥾 **{Name}** — {Distanz}, {Dauer}, {Schwierigkeit}. ⭐ {Rating} ({N} Reviews). {Description}. [Waymarked Trails]({URL}) · [GPX ↓]({download-URL})
  - 🍷 **Einkehr:** {Restaurant/Bar} — {Beschreibung}.
```

Rules:

- GPX download URL format: `https://hiking.waymarkedtrails.org/api/details/relation/{id}/gpx`
- One-way routes: flag with `⚠️ One-way` + describe return transport.
- Swimming at endpoint: note inline with 🏊.
- Einkehr: list refreshment options at start, endpoint, or midpoint.
- Every day should have at least one hiking option (short walk 2–3 Std. if no major hike).

## Swimming / Bathing

```markdown
- 🏊 **{Name}** [📍]({Google Maps link}) — {Type: Strand/Fluss/Therme/Felstöpfe}. {Brief description}.
```

- Check swimming options for all driving days (unterwegs stops).
- Include river pools, thermal springs, rock pools — not just beaches.

## Map Generation Workflow

Use these tools in sequence for each driving day:

```bash
# 1. Create GPX with all waypoints (including detour/swim stops)
mcp_osrm_route_to_gpx(waypoints=[[lon,lat], ...], output_path="trips/road/{trip-name}/gpx/{start}-{ziel}.gpx")

# 2. Render map with stations and POIs
python scripts/render_roadtrip_map.py trips/road/{trip-name}/gpx/{start}-{ziel}.gpx trips/road/{trip-name}/img/{start}-{ziel}.png \
  --stations 'Label:lon,lat' ... \
  --pois 'category:name:lon,lat' ...
```

### render_roadtrip_map.py Parameters

- `--stations 'Name:lon,lat'` — Major stops shown as labeled circle markers. Use day-prefixed labels like `T1 Bilbao`.
- `--pois 'category:name:lon,lat'` — POI icons on map. Valid categories: `art`, `hike`, `swim`, `food`, `wine`, `sight`, `nature`, `coffee`.
- `--width` / `--height` — Image dimensions (default: 900×600).

### Critical Map Rule

Every stop mentioned in the day's text MUST appear as a station or POI marker on the map. No stop without a marker. Combine labels when POIs are close (e.g., "Urdaibai / Playa de Laga").

## Section 3: Erweiterungsideen (optional)

Brief notes on possible route extensions with best season.

## Section 4: Quellen

Table format for trail sources:

```markdown
| Route  | Länge  | Link                         | GPX            |
| ------ | ------ | ---------------------------- | -------------- |
| {Name} | {X} km | [waymarkedtrails.org]({URL}) | [↓]({GPX-URL}) |
```

Include Wikivoyage sources and tour operator inspiration links.

## Language

All trip content is written in **German**. Use German weekday names, date formats (TT.MM.YYYY or "DD. Monat"), and descriptions.
