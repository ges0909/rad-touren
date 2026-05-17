---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Output Template

Every trip file MUST start with empty YAML front matter (`---\n---\n`). Sections separated by `---` horizontal rules.

## 1. Title + Compact Header

```markdown
# {Destination} Roadtrip

**Reisezeitraum:** {Wochentag} {Datum von} – {Wochentag} {Datum bis} · {N} Tage · ~{X} km (inkl. Tagesausflüge)
**Flug:** BER ↔ {Airport}, Direktflug {Airline} (nur {Flugtage}, {Tageszeit})
**Mietwagen:** Übernahme {Datum} ({Ort}) / Abgabe {Datum} ({Ort}) — {N} Tage

> 🌊 {One-line trip highlight — what makes this destination special}

> ☀️ **Wetter:** {Temperaturbereich}, Regen {X}%. {Saisonaler Hinweis}.

> 🇪🇸 **Länderinfo:** {Preisniveau}. Tempolimit: {X} / {Y} / {Z} km/h. {Besonderheiten}. Notruf {N}. {Lokale Bräuche}.
```

Rules:

- No separate chapters for Wetter, Anreise, Kostenübersicht, Tipps — integrate into header
- No duration in title (implicit from dates)
- Weekdays in Reisezeitraum
- Flight times noted at Tag 1 (Hinflug) and last day (Rückflug)

## 2. Reiseverlauf

One H3 (`###`) per day. All days same heading level.

### Driving days (transfer between cities)

```markdown
### Tag {N} · {Wochentag} {Datum} · {Von} → {Ziel} · {X} km, ~{Y} Std.

![Tag {N}: {Von} → {Ziel}](img/{von}-{ziel}.png)
[Route in Google Maps](https://www.google.com/maps/dir/{Von}/{Stopp1}/{Stopp2}/{Ziel})

{Fahrtbeschreibung / Unterwegs-Stopps}

**Unterkunft:** [{Name}]({booking.com-URL}) ({Rating}, ~{N} Reviews) — {Beschreibung} (~{X}–{Y} €/Nacht)

- 🥾 **{Wanderung}** — {Details}
- 🏊 **{Badestelle}** — {Details}
- 🍷 **{Restaurant}** — {Details}
```

### Stay days (no driving)

```markdown
### Tag {N} · {Wochentag} {Datum} · {Ort}

- 🥾 **{Wanderung}** — {Details}
- 🎨 **[{Museum}]({URL})** — {Details}. (~{X} €/P.)
```

### Day trips

```markdown
### Tag {N} · {Wochentag} {Datum} · {Ziel} (Tagesausflug, {X} Min.)
```

## 3. Day Structure Rules

**Chronological order within each day** — activities listed in the sequence they happen:

1. Fahrt / Unterwegs-Stopps (morning)
2. **Unterkunft** (check-in, placed after arrival)
3. Aktivitäten am Zielort (afternoon/evening)

For arrival day: Flug → Transfer → Unterkunft → Abendessen
For departure day: Aktivitäten → Fahrt zum Flughafen → Rückflug

## 4. Route Maps

Every driving day gets a route map + Google Maps link:

```bash
# 1. Create GPX with all waypoints (including swim/detour stops)
mcp_osrm_route_to_gpx(waypoints=[...], output_path="trips/road/gpx/{start}-{ziel}.gpx")

# 2. Render map — EVERY stop mentioned in text must appear as station
python scripts/render_roadtrip_map.py trips/road/gpx/{start}-{ziel}.gpx trips/road/img/{start}-{ziel}.png \
  --stations '{Name}:{lon},{lat}' ...
```

**Critical rule:** Every stop mentioned in the day's text MUST be visible on the map. No stop without marker. Use combined labels when POIs are close (e.g., "Urdaibai / Playa de Laga").

File naming: `{start}-{ziel}.gpx` / `{start}-{ziel}.png` (kebab-case, ASCII-safe).

## 5. POI Formatting

```markdown
- {emoji} **[{Name}]({description-URL})** [📍](https://www.google.com/maps/search/?api=1&query={lat},{lon}) — {Description}. (~{X} €/P., {opening hours})
```

Rules:

- **Description link**: Official website or tourism page for "what to expect" info
- **📍 Navigation pin**: Google Maps coordinate link for POIs requiring driving (not walkable from accommodation)
- **Entry price**: Append `(~{X} €/P.)` when applicable
- **Opening hours**: Append closure days inline `(Di–So, Mo geschlossen)`
- **Advance booking**: `⚠️ Tickets vorab online buchen`
- Prioritize by interest order: Wandern → Baden → Küche → Gärten → Kunst

## 6. Hiking Routes

```markdown
- 🥾 **{Name}** — {Distanz}, {Dauer}, {Schwierigkeit}. ⭐ {Rating} ({N} Reviews). {Description}. [Waymarked Trails]({URL}) · [GPX ↓]({download-URL})
  - 🍷 **Einkehr:** {Restaurant/Bar am Start/Ziel/Wendepunkt} — {Beschreibung}.
```

Rules:

- **GPX download**: Always include when Waymarked Trails route ID available. Format: `https://hiking.waymarkedtrails.org/api/details/relation/{id}/gpx`
- **One-way routes**: Flag with `⚠️ One-way` + describe transport for return (bus line, link to timetable)
- **Swimming at endpoint**: Note with 🏊 inline if trail ends at beach/river
- **Einkehr**: List refreshment options (bar, restaurant, hut) at start, endpoint, or midpoint with brief description
- **Every day should have a hiking option** — if no major hike, suggest a short walk (2–3 Std.)

## 7. Swimming / Bathing

```markdown
- 🏊 **{Name}** [📍]({Google Maps link}) — {Type: Strand/Fluss/Therme/Felstöpfe}. {Brief description}.
```

Rules:

- Check swimming options for ALL driving days (unterwegs stops)
- Include river pools, thermal springs, rock pools — not just beaches
- Add 📍 pin for spots requiring driving

## 8. Accommodation

```markdown
**Unterkunft:** [{Name}]({booking.com-direct-URL}) ({Rating}, ~{N} Reviews) — {Description} (~{X}–{Y} €/Nacht)
```

Rules:

- Always link directly to booking.com hotel page
- Placed chronologically (after arrival, before evening activities)

## 9. Erweiterungsideen (optional)

Brief notes on route extensions with best season.

## 10. Quellen

Waymarked Trails links with GPX column, Wikivoyage sources, tour operator inspiration.

```markdown
| Route  | Länge  | Link                         | GPX            |
| ------ | ------ | ---------------------------- | -------------- |
| {Name} | {X} km | [waymarkedtrails.org]({URL}) | [↓]({GPX-URL}) |
```
