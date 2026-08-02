---
inclusion: fileMatch
fileMatchPattern: "trips/hike/**"
---

# Hiking Preferences — Berlin/Brandenburg Tageswanderungen

Persönliche Präferenzen für Wanderungen. Diese Datei ergänzt `user-preferences.md` (universelle Regeln). Technische Workflow-Regeln folgen in `hike-planner.md` (noch nicht implementiert).

## Tour Profile

| Eigenschaft      | Wert                                      |
| ---------------- | ----------------------------------------- |
| Distanz          | 10–20 km                                  |
| Dauer            | 3–5 Stunden reine Gehzeit                 |
| Schwierigkeit    | Moderat (auch für ungeübte Wanderer)      |
| Höhenmeter       | Max. 500 m Gesamtsteigung                 |
| Rückreise        | Bis 18:00 Uhr am Startbahnhof             |
| Verkehrsmittel   | Regionalzüge (S-Bahn, RB, RE)             |
| Gruppe           | 2 Personen                                |
| Abfahrt          | ~09:00 Uhr                                |

## Interests — Priorität (Tageswanderungen)

Diese Prioritätsreihenfolge für Wanderungen verwenden. Bei mehreren Interests pro Location höchste Priorität zuerst nennen.

| #   | Emoji | Interest          | Verhalten                                                                                           |
| --- | ----- | ----------------- | --------------------------------------------------------------------------------------------------- |
| 1   | 🥾    | Wanderwege        | **Highest priority.** Markierte Routen bevorzugt. Rating ≥4.0 (≥30 Reviews, AllTrails/Komoot).      |
| 2   | 🌿    | Natur & Parks     | Naturschutzgebiete, Nationalparks, Landschaftsparks, botanische Gärten.                             |
| 3   | 🏊    | Baden             | Seen, Naturbadestellen als optionaler Zwischen-/Endpunkt (Sommer).                                  |
| 4   | 🏛️    | Sehenswürdigkeiten| Burgen, Klöster, Aussichtstürme entlang der Route.                                                  |
| 5   | 🍷    | Einkehr           | Gaststätten, Cafés am Start/Ziel oder als Mittags-Stop.                                             |

**Anwendung:**
- Waymarked Trails für offizielle markierte Routen nutzen
- Bewertungen immer nachschlagen (AllTrails, Komoot, Wikiloc)
- Pro Tour: 1 Hauptwanderweg, 1–2 Natur-Highlights, 1 Einkehr-Option

## Route Selection

Bevorzugt markierte, offizielle Wanderwege:

- **Fernwanderwege** (z.B. 66-Seen-Weg, Märkischer Landweg) — Tagesetappen
- **Rundwanderwege** (Rückkehr zum Start bevorzugt)
- **Qualitätswege** (z.B. "Qualitätsweg Wanderbares Deutschland")

**Rating-Schwelle:**
- Bevorzugt: ≥4.0 Sterne mit ≥30 Bewertungen
- Verwerfen: <3.5 Sterne oder <10 Bewertungen (außer keine Alternative)

**Quellen:**
1. Waymarked Trails (`search_routes`, `get_route_details`)
2. AllTrails / Komoot (Web-Suche für Bewertungen)
3. Lokale Tourismusverbände (Brandenburg Tourismus, TMB)

## Terrain & Difficulty

- **Wegebeschaffenheit:** Naturpfade bevorzugt, asphaltierte Abschnitte minimieren
- **Trittsicherheit:** Nicht erforderlich (moderate Wege)
- **Kondition:** Durchschnittlich (keine Bergwander-Erfahrung nötig)
- **Steigungen:** Moderat, keine steilen Anstiege
- **Barrierefreiheit:** Erwähnen wenn vorhanden (für zukünftige Planung)

## Food & Drink (Tageswanderungen)

Regeln für Einkehr-Empfehlungen:

1. **Wandergaststätten bevorzugt** — Hofcafés, Landgasthäuser, Waldgaststätten
2. **Brotzeit-Optionen** — Picknick-Plätze mit Aussicht erwähnen
3. Regional/traditionell über modern
4. Rating-Schwelle: ≥4.0 auf Google Maps (mind. 30 Bewertungen)
5. Öffnungszeiten prüfen (viele Wandergaststätten Mo/Di geschlossen)

**Beispiele:**
- ✅ Forsthaus, Berggasthof, Hofcafé, Klosterschänke
- ✅ Picknick-Platz mit Aussicht (eigene Verpflegung)
- ❌ Fast Food, Imbiss-Ketten

**Format:**
```
### 🍷 Einkehr: Forsthaus Bürgerheide

- **Lage:** Km 8.5 der Route, direkter Wegstop
- **Spezialität:** Brandenburger Wildgerichte, hausgemachter Kuchen
- **Rating:** ⭐ 4.3/5 (62 Bewertungen, Google Maps)
- **Öffnung:** Mi–So 11:00–19:00, Mo/Di Ruhetag
- **Website:** [forsthaus-buergerheide.de](https://...)
- ℹ️ Zuletzt geprüft: 2026-08-02
```

## Accommodation

Nicht relevant für Tageswanderungen (Rückkehr am selben Tag).

## Equipment & Preparation

Nicht in Tour-Beschreibung aufnehmen (User-Eigenverantwortung), aber bei Bedarf erwähnen:

- **Wetter:** Prognose für Tour-Tag angeben
- **Wasserquellen:** Trinkbrunnen/Quellen entlang Route erwähnen
- **Mobilfunk:** Funklöcher kennzeichnen falls bekannt
- **Notfallinfo:** Nächste Ortschaft/Bahnhof bei langen Waldabschnitten

## Seasonal Awareness

- **Beste Zeit:** April–Oktober (außerhalb: Wetter/Tageslicht-Einschränkungen erwähnen)
- **Waldbrandgefahr:** Sommer (besonders Brandenburg) — bei Warnstufe 4/5 erwähnen
- **Badesaison:** Mai–September (außerhalb: Wassertemperatur angeben)
- **Herbst/Winter:** Früher Sonnenuntergang beachten (Rückkehr bis 16:00 empfehlen)
