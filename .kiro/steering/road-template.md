---
inclusion: fileMatch
fileMatchPattern: "trips/road/**"
---

# Roadtrip Output Template

Every trip file MUST start with empty YAML front matter (`---\n---\n`). Sections separated by `---` horizontal rules.

## 1. Title + Metadata + Map

```markdown
# {Destination} Roadtrip ({N} Tage)

**Reisezeitraum:** {Datum von} – {Datum bis}
**Dauer:** {N} Tage / {N-1} Nächte
**Stationen:** {N} Stopps
**Gesamtstrecke:** ~{X} km
**Flug:** BER → {Airport} (Hin) / {Airport} → BER (Rück)
**Mietwagen:** Übernahme/Abgabe {Airport}

> {emoji} **Tipp:** {one-line highlight}

[![Routenkarte](img/{name}.png)](img/{name}.png)
```

Map directly after metadata for immediate visual overview. Rendered via `scripts/render_roadtrip_map.py` with `--stations` (day labels) and `--pois` (icons + legend overlay).

## 2. Routenplanung (combined day-by-day table)

The **primary structure** — a single table combining route, days, and activities.

```markdown
## Routenplanung

{Stadt 1} → {Stopp 2} → … → {Stadt 1}

| Tag | Datum             | Station                            | Programm                  |
| --- | ----------------- | ---------------------------------- | ------------------------- |
| 1   | {Wochentag Datum} | **{Ort}** (Ankunft)                | {Kurzbeschreibung}        |
| 2   | {Wochentag Datum} | 🚗 → **{Ort}** · {X} km, ~{Y} Std. | {Stopps + Aktivitäten}    |
| 3   | {Wochentag Datum} | {Ort}                              | {🥾 🏊 🎨 🍷 Aktivitäten} |
```

Table rules:

- **Driving days**: `🚗 → **destination** · distance, duration`
- **Stay days**: station name only (no 🚗)
- **Day trips**: `{destination} (Tagesausflug, {X} Min.)`
- **No night counts** — implicit from consecutive days at same station
- Use emoji from interest table in Programm column
- Bold the **key highlight** of each day

Below the table:

```markdown
> ⚠️ **Längste Etappe:** Tag {N}, {A} → {B} ({X} km, ~{Y} Std.).
> 💡 **Flexibilität:** {weather alternatives}
```

## 3. Stationen & POIs (compact reference)

One H3 per station. **No prose, no subsection headers.** Flat POI list with emoji + one-line description.

```markdown
## Stationen & POIs

### {Ortsname} ({N} Nächte)

**Unterkunft:** {Name} ({rating}, ~{N} Reviews) — {Beschreibung}, Frühstück inkl. (~{X}–{Y} €/Nacht, booking.com)

- 🥾 **{Wanderung}** — {Distanz}, {Dauer}, {Schwierigkeit}. ⭐ {Rating} ({N} Reviews).
- 🏊 **{Badestelle}** — {Kurz.}
- 🍷 **{Restaurant}** — {Spezialität.}
- 🌿 **[{Garten}]({URL})** — {Kurz.}
- 🎨 **[{Museum}]({URL})** — {Kurz.}
- 🏛️ **{Sehenswürdigkeit}** — {Kurz.}
- 🍇 **[{Weingut}]({URL})** — {Kurz.}
```

Rules:

- Prioritize by interest order from user-preferences (Wandern → Baden → Küche → Gärten → Kunst)
- Hyperlinks for major POIs (official websites only)
- Include ratings for hiking routes and accommodations
- Deduplicate within 200 m
- "Unterwegs" POIs listed at the station you arrive at
- **Practical hints** — append inline where relevant:
  - Weekly closures: `(Do–Mo, Di+Mi geschlossen)`
  - Advance booking: `⚠️ Tickets vorab online buchen`
  - Seasonal restrictions: `(nur Mai–Okt)` or `(Zufahrt im Sommer nur per Bus)`
  - These hints go at the end of the POI line, after the description.

## 4. Wetter

```markdown
## Wetter

> ℹ️ _{Seasonal context. Aktuelle Vorhersage prüfen._

| Station | Temperatur | Regen | Besonderheiten |
| ------- | ---------- | ----- | -------------- |
```

## 5. Anreise & Mietwagen

```markdown
## Anreise & Mietwagen

**Hinflug:** BER → {Airport}, ~{X} Std. {Airline.}
**Rückflug:** {Airport} → BER, ~{X} Std.

**Mietwagen:** Kompaktwagen, ~{X}–{Y} € für {N} Tage (Vollkasko inkl.)

> 💡 Frühzeitig buchen: billiger-mietwagen.de
```

## 6. Kostenübersicht

```markdown
## Kostenübersicht (2 Personen)

| Posten              | Geschätzt      |
| ------------------- | -------------- |
| Flüge (2×)          | ~{X}–{Y} €     |
| Mietwagen           | ~{X}–{Y} €     |
| Unterkünfte         | ~{X}–{Y} €     |
| Benzin              | ~{X}–{Y} €     |
| Essen & Aktivitäten | ~{X}–{Y} €     |
| **Gesamt**          | **~{X}–{Y} €** |
```

## 7. Tipps & Länderinfo

```markdown
## Tipps & Länderinfo

**Packliste:** {trip-specific}
**Lokale Bräuche:** {customs}

| Thema              | Info                                              |
| ------------------ | ------------------------------------------------- |
| **Preisniveau**    | {vs. Deutschland}                                 |
| **Tempolimit**     | Innerorts {X}, Landstraße {Y}, Autobahn {Z} km/h  |
| **Besonderheiten** | {Maut, Lichtpflicht, etc.}                        |
| **Reisehinweise**  | {Status} ([Auswärtiges Amt](...))                 |
| **Notruf**         | {Notrufnummern inkl. Bergrettung falls vorhanden} |
```

## 8. Erweiterungsideen (optional)

Brief notes on route extensions with best season.

## 9. Quellen

Waymarked Trails links, Wikivoyage sources, tour operator inspiration.
