---
inclusion: fileMatch
fileMatchPattern: "trips/**"
---

# Reiseplanung mit Gerrit on Tour

Universelle Vorgaben für alle Reisetypen (Cycling, Hiking, Roadtrips). Reisetyp-spezifische Präferenzen sind in separaten Dateien organisiert.

## Home Base & Travel Group

- **Home base:** S Blankenfelde (TF) Bhf, Berlin
- **Reisegruppe:** 2 Personen (default)
- **Reisetypen:**
  - 🚴 Cycling: Tagestouren (siehe `bike-preferences.md`)
  - 🥾 Hiking: Tageswanderungen (geplant, siehe `hike-preferences.md`)
  - 🚗 Roadtrips: Mehrtagstrips (siehe `road-preferences.md`)

## Response Language

- Output language is controlled by the UI language toggle (DE/EN). Follow the system prompt language instruction.
- Code artifacts (file names, GPX metadata, MCP tool parameters, commit messages) are always in English using kebab-case.

## Interests — Grundkategorien

Diese Kategorien gelten für alle Reisetypen. Die Prioritätsreihenfolge und Anwendung ist reisetyp-spezifisch definiert.

| Emoji | Interest           | Beschreibung                                           |
| ----- | ------------------ | ------------------------------------------------------ |
| 🥾    | Wandern            | Wanderwege, Naturpfade, Aussichtspunkte                |
| 🏊    | Baden              | Seen, Strände, Thermen, Naturbadestellen               |
| 🍷    | Regionale Küche    | Lokale Restaurants, Märkte, Food-Spezialitäten         |
| 🌿    | Botanische Gärten  | Botanische Gärten, Arboreten, Landschaftsparks         |
| 🎨    | Moderne Kunst      | Galerien, Skulpturenparks, zeitgenössische Kunstmuseen |
| 🏛️    | Sehenswürdigkeiten | Historische Stätten, Denkmäler, Museen                 |

**Verwendung:**

- Verwende die Emojis aus dieser Tabelle konsistent in allen Tour-Dokumenten
- Bei mehreren Kategorien pro Location: höchste Priorität zuerst
- Prioritätsreihenfolge: siehe reisetyp-spezifische Präferenz-Datei

## Content Integrity

Diese Regeln sind nicht verhandelbar für alle generierten Inhalte:

| Rule               | Requirement                                                                                        |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| No fabrication     | Nur Daten aus API-Ergebnissen oder Web-Suche präsentieren. Falls nicht verfügbar, explizit angeben |
| Emoji consistency  | Interest-Tabelle Emojis für POIs verwenden. 🍺 für Biergärten/Restaurants (Overpass `einkehr`)     |
| Deduplication      | Ein Eintrag pro POI; Duplikate im 200 m Radius entfernen                                           |
| Seasonal awareness | Schließungen, eingeschränkte Öffnungszeiten, Off-Season-Risiken kennzeichnen                       |
| Source attribution | `ℹ️ Zuletzt geprüft: {date}` für web-basierte Daten anhängen                                       |
| Links              | Nur offizielle Websites für große POIs. Keine Google Maps, TripAdvisor oder temporäre URLs         |
| Link verification  | Vor Einfügen jeder URL: HTTP 200 via `web_fetch` prüfen. Tote Links entfernen/ersetzen             |
| Unverifiable data  | Mit `ℹ️ Nicht verifiziert.` markieren — niemals Details raten oder erfinden                        |

## Route Discovery & Reviews

### Waymarked Trails (offiziell markierte Routen)

Diese MCP-Tools in Reihenfolge für Route-Recherche verwenden:

1. `search_routes(query, activity)` — Routen nach Name, Region oder Keyword finden
2. `get_route_details(route_id, activity)` — Länge, Markierungen, Betreiber abrufen
3. `get_route_segments(route_id, activity)` — Etappen und Orte entlang der Route

### Review Lookup (Web-Suche)

**Immer Bewertungen nachschlagen bei Wanderrouten-Vorschlägen.** Diese Schwellenwerte anwenden:

- Bevorzugt: ≥4.0 Sterne mit ≥30 Bewertungen
- Verwerfen: <3.5 Sterne oder <10 Bewertungen (außer keine Alternative)

Vorgehen:

1. Suche: `"{route name}" AllTrails review`
2. Suche: `"{route name}" Komoot Bewertung`
3. Suche: `"{route name}" Wikiloc rating` (besonders Spanien/Portugal)
4. Zusammenfassen: Bewertung, Lob/Kritik, Schwierigkeit, Wegebeschaffenheit
5. Markieren: `ℹ️ Bewertungen aus Web-Recherche ({date}), nicht per API verifiziert.`

### Tool Selection Guide

| Intent                 | Tool                                                   |
| ---------------------- | ------------------------------------------------------ |
| Routen in einer Region | Waymarked Trails `search_routes`                       |
| Routen-Empfehlung      | Waymarked Trails `search_routes` + `get_route_details` |
| Routen-Rating/Review   | Web search (AllTrails/Komoot)                          |
| Custom Cycling Tour    | BRouter `calculate_route`                              |
| Custom Car/Hiking Tour | OpenRouteService `calculate_route`                     |
| Erfahrungsberichte     | Web search (Komoot/AllTrails/Outdooractive)            |

## Output-Format

Jede Tour-Anfrage produziert:

- Markdown-Dokument (`trips/{type}/{tour-name}/index.md`)
- GPX-Track(s) (`gpx/{segment-name}.gpx`)
- Routenkarte als PNG (`img/route-map.png`)
- Zusätzliche Outputs sind reisetyp-spezifisch definiert
