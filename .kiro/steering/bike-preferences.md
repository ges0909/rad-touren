---
inclusion: fileMatch
fileMatchPattern: "trips/bike/**"
---

# Bike Tour Preferences — Berlin/Brandenburg Tagestouren

Persönliche Präferenzen für Radtouren. Diese Datei ergänzt `user-preferences.md` (universelle Regeln) und `bike-planner.md` (technische Workflow-Regeln).

## Tour Profile

| Eigenschaft      | Wert                                      |
| ---------------- | ----------------------------------------- |
| Distanz          | 40–80 km (ideal: 55–65 km)                |
| Dauer            | 4–6 Stunden reine Fahrzeit                |
| Terrain          | Flach bevorzugt, max. 400 m Gesamtsteigung |
| Rückreise        | Bis 18:00 Uhr am Startbahnhof             |
| Verkehrsmittel   | Regionalzüge (S-Bahn, RB, RE)             |
| Gruppe           | 2 Personen + 2 Fahrräder (VBB-Fahrpreis) |
| Abfahrt          | ~09:00 Uhr                                |

## Interests — Priorität (Tagestouren)

Diese Prioritätsreihenfolge für Radtouren verwenden. Bei mehreren Interests pro Location höchste Priorität zuerst nennen.

| #   | Emoji | Interest          | Verhalten                                                                                           |
| --- | ----- | ----------------- | --------------------------------------------------------------------------------------------------- |
| 1   | 🏊    | Baden             | **Highest priority.** Seen, Strände, Naturbadestellen. Ideal als Mittags-/Nachmittagsstop.         |
| 2   | 🍷    | Einkehr           | Biergärten, Cafés, regionale Küche. Mittag- oder Endpunkt.                                          |
| 3   | 🌿    | Botanische Gärten | Immer erwähnen wenn in Route-Nähe (max. 2 km Umweg).                                                 |
| 4   | 🎨    | Moderne Kunst     | Galerien, Skulpturenparks. Erwähnen wenn auf Route oder <1 km Umweg.                                |
| 5   | 🏛️    | Sehenswürdigkeiten| Burgen, Klöster, historische Stadtkerne. Kurzer Stop (15–30 min).                                   |

**Anwendung:**
- Overpass-Presets: `badestellen`, `einkehr`, `sehenswuerdigkeiten`, `kunst`
- Baden-POIs besonders hervorheben (Emoji + „**Badestopp**" im Text)
- Pro Tour: 1–2 Badestellen, 2–3 Einkehr-Optionen, 3–5 Sehenswürdigkeiten

## Food & Drink (Tagestouren)

Regeln für Restaurant-/Food-Empfehlungen:

1. **Spontan zugänglich** — keine Reservierung nötig, kurze Wartezeiten
2. **Biergärten bevorzugt** — Außenplätze, lockere Atmosphäre
3. Regionale Küche über internationale Ketten
4. **Nie** Fast Food oder Ketten empfehlen
5. Rating-Schwelle: ≥4.0 auf Google Maps (mind. 30 Bewertungen). Immer Rating angeben.
6. Öffnungszeiten prüfen (Montag oft Ruhetag)

**Beispiele:**
- ✅ Landgasthof, Hofcafé, Strandcafé, Biergarten
- ✅ Fischbude (an Seen), Bäckerei/Konditorei mit Sitzplätzen
- ❌ McDonald's, Subway, Nordsee (Kette)

**Format:**
```
### 🍷 Mittagspause: Landgasthof Alter Krug

- **Lage:** Direkter Routenstop in Beeskow
- **Spezialität:** Spreewälder Küche, Fischgerichte
- **Rating:** ⭐ 4.2/5 (87 Bewertungen, Google Maps)
- **Öffnung:** Mi–So 11:00–21:00, Mo/Di Ruhetag
- **Website:** [alter-krug-beeskow.de](https://...)
- ℹ️ Zuletzt geprüft: 2026-08-02
```

## Accommodation

Nicht relevant für Tagestouren (Rückkehr am selben Tag).

## POI Density & Presentation

- **Badestellen:** Alle innerhalb 1 km Umweg erwähnen, beste 1–2 hervorheben
- **Einkehr:** 2–3 Optionen entlang Route (Morgen-Kaffee, Mittag, Nachmittag)
- **Sehenswürdigkeiten:** Top 3–5 erwähnen, kurze Beschreibung (2–3 Sätze)
- **Radservice:** Nur erwähnen wenn in Start-/Zielort oder bei bekannten Problemstellen

## Seasonal Awareness

- **Badesaison:** Mai–September (außerhalb: Wassertemperatur angeben, Baden einschränken)
- **Biergärten:** April–Oktober (Winteröffnung explizit prüfen)
- **Öffnungszeiten:** Immer aktuelle Zeiten web-basiert verifizieren
- **Wetter:** Prognose für Tour-Tag abrufen, Regenrisiko kennzeichnen
