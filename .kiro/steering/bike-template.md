---
inclusion: fileMatch
fileMatchPattern: "trips/bike/**"
---

# Bike Tour Output Template

Every tour file MUST start with empty YAML front matter (`---\n---\n`) and contain these sections in order, separated by `---` horizontal rules. Omit section 6 (Badestellen) if no swimming spots exist.

## 1. Title

```markdown
# {Tour-Name}-Runde ab {Start/Ziel}
```

## 2. Metadata Block

```markdown
**Distanz:** ~{X} km ({X} km lt. BRouter)
**Fahrzeit:** ca. {X}–{Y} Std. (ohne Pausen)
**Routentyp:** Rundtour, {terrain}
**Start/Ziel:** {Station name}
**GPX-Datei:** [gpx/{name}.gpx](gpx/{name}.gpx)
```

## 3. Tip Box

```markdown
> {emoji} **Tipp:** {one-line highlight of the tour}
```

Emoji by theme: 🏛️ culture, 🌿 nature, 🌸 seasonal, 🌊 water/lakes, 🌲 forest.

## 4. Streckenverlauf

```markdown
## Streckenverlauf

{Start} → {Waypoint 1} → {Waypoint 2} → … → {Start}

[![{Tour-Name} Karte](img/{name}.png)](img/{name}.png)

[![Höhenprofil](img/{name}-elevation.png)](img/{name}-elevation.png)
```

## 5. Streckenabschnitte

One H3 per segment. Include only POI types that actually exist along that segment:

```markdown
## Streckenabschnitte

### {N}. {Von} → {Nach} (ca. {X} km)

{Description with path/street names in **bold**. Mention named cycling routes where applicable.}

🏛️ **{Name}** — {short description}
🎨 **{Name}** — {short description}
🍺 {Café/restaurant name} — {short description}
🏊 **{Name}** — {short description}
```

## 6. Badestellen (optional — omit if none)

```markdown
## Badestellen

- 🏊 **{Name}** — {description}
```

## 7. Einkehrmöglichkeiten

Summary of all food/drink stops mentioned in the segment descriptions.

## 8. Wetter

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

Add warnings below the table for notable conditions (heat, rain, storms).

## 9. Veranstaltungen

Events near the route on the tour date. Always include this section — add a note if none found.

## 10. Nahverkehrsanbindung

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

## Fare Calculation Rules

- `get_journeys` returns Regionaltarif fares automatically (distance-based, use as-is)
- For Berlin ABC fares, use the reference table below
- Always calculate for **2 persons + 2 bicycles**
- Einzelfahrt is per direction (Hin+Rück = 2×); Tageskarte covers both ways
- Determine tariff zone: stations like Strausberg, Eberswalde, Königs Wusterhausen use Regionaltarif (API prices). Berlin-area stations use ABC tariff (table below).

## VBB Fare Reference (Berlin ABC)

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
