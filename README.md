# 🗺️ Tour Planning — Cycling, Hiking & Roadtrips

KI-gestützte Tourenplanung mit [Kiro](https://kiro.dev) und eigenen MCP-Servern für Routing, Wetter, POIs, ÖPNV und Reiseführer-Inhalte.

| Kategorie    | Beschreibung                                       | Status  |
| ------------ | -------------------------------------------------- | ------- |
| 🚴 Cycling   | Tagestouren in Berlin/Brandenburg per Regionalbahn | Aktiv   |
| 🥾 Hiking    | Tageswanderungen in Berlin/Brandenburg             | Geplant |
| 🚗 Roadtrips | Mehrtägige Mietwagen-Trips durch Europa            | Aktiv   |

**→ [Radtouren](planning/bike/README.md)** · **→ [Roadtrips](planning/road/README.md)**

---

## Quickstart

Voraussetzungen: [Kiro](https://kiro.dev) + [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# Alle MCP-Server installieren
for dir in mcp/brouter mcp/ors mcp/osrm mcp/open-meteo mcp/vbb mcp/overpass mcp/waymarkedtrails mcp/wikivoyage; do
  uv sync --directory "$dir"
done
```

```bash
# API Key für OpenRouteService (.env wird gitignored)
echo "ORS_API_KEY=dein-key-hier" > .env
```

Kostenlosen Key gibt's bei [openrouteservice.org](https://openrouteservice.org/dev/#/signup). Alle anderen Server nutzen freie APIs ohne Key.

---

## Wie es funktioniert

Ein einzelner Prompt wie _„Plane eine 50-km-Tour durch den Spreewald"_ oder _„Plane einen 2-Wochen-Roadtrip durch Nordspanien"_ erzeugt ein vollständiges Tour-Dokument mit Route, Karte, POIs, Wetter und Verbindungen.

Dafür sorgen drei Bausteine:

### Steering Files

Steering-Dateien machen Kiro zum domänenspezifischen Tourenplaner:

| Datei                      | Scope              | Funktion                                           |
| -------------------------- | ------------------ | -------------------------------------------------- |
| `user-preferences.md`      | Immer              | Interessen, Essens-/Unterkunftsregeln, Reisegruppe |
| `cycling-tour-planning.md` | `planning/bike/**` | Rad-Workflow, BRouter-Routing, VBB-Tarife          |
| `roadtrip-planning.md`     | `planning/road/**` | Roadtrip-Workflow, ORS-Routing, Pufferregel        |
| `commit-messages.md`       | Immer              | Conventional Commits                               |

### MCP Server

Sieben eigene Python-Server (FastMCP + httpx), kein Node.js:

| Server                                    | Funktion                                       | API                                                                              |
| ----------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------- |
| [`brouter`](mcp/brouter/)                 | Rad-/Wanderrouting, Geocoding, Kartenrendering | [BRouter](https://brouter.de) + [Nominatim](https://nominatim.openstreetmap.org) |
| [`ors`](mcp/ors/)                         | Auto-/Rad-/Fußrouting, Isochrone, Matrix       | [OpenRouteService](https://openrouteservice.org/)                                |
| [`osrm`](mcp/osrm/)                       | Auto-Routing mit GPX-Export (Straßengeometrie) | [OSRM](https://project-osrm.org/) (public, kein Key)                             |
| [`open-meteo`](mcp/open-meteo/)           | Wettervorhersage + Geocoding                   | [Open-Meteo](https://open-meteo.com/)                                            |
| [`vbb`](mcp/vbb/)                         | Haltestellensuche, Abfahrten, Verbindungen     | [VBB REST](https://v6.vbb.transport.rest/)                                       |
| [`overpass`](mcp/overpass/)               | POI-Suche entlang von Routen                   | [Overpass API](https://overpass-api.de/)                                         |
| [`waymarkedtrails`](mcp/waymarkedtrails/) | Markierte Wander- & Radrouten finden           | [Waymarked Trails](https://waymarkedtrails.org/)                                 |
| [`wikivoyage`](mcp/wikivoyage/)           | Reiseführer, Zielsuche, Umkreissuche           | [Wikivoyage](https://de.wikivoyage.org/)                                         |

Zusätzlich wird `remote_web_search` genutzt für Flüge, Hotels, Mietwagen und Events — dort existiert keine stabile freie API.

### Hooks

| Hook                  | Trigger                                                      | Aktion                                                   |
| --------------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| GPX Consistency Check | GPX-Datei in `planning/bike/` oder `planning/hike/` geändert | Karte + Höhenprofil neu rendern, Distanzen aktualisieren |

---

## Projektstruktur

```
planning/
├── bike/                    Radtouren: Markdown, GPX, Karten
├── hike/                    Wandertouren (geplant)
└── road/                    Mehrtägige Auto-Trips
mcp/
├── brouter/                 Rad-/Wanderrouting + Karten
├── ors/                     Auto-Routing (OpenRouteService)
├── osrm/                    Auto-Routing + GPX-Export (OSRM)
├── open-meteo/              Wetter
├── overpass/                POI-Suche (OpenStreetMap)
├── vbb/                     ÖPNV Berlin/Brandenburg
├── waymarkedtrails/         Markierte Wander-/Radrouten
└── wikivoyage/              Reiseführer-Inhalte
.kiro/
├── settings/mcp.json        Server-Konfiguration
├── hooks/                   Agent Hooks
└── steering/                Steering-Regeln
.env                         API Keys (gitignored)
```

## Tests

```bash
uv run --directory mcp/brouter pytest -v
uv run --directory mcp/open-meteo pytest -v
uv run --directory mcp/vbb pytest -v
uv run --directory mcp/overpass pytest -v
uv run --directory mcp/waymarkedtrails pytest -v
uv run --directory mcp/wikivoyage pytest -v
```

## Lizenzen & Datenquellen

| Quelle                                                   | Lizenz       |
| -------------------------------------------------------- | ------------ |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | ODbL         |
| [BRouter](https://brouter.de)                            | MIT          |
| [OpenRouteService](https://openrouteservice.org/)        | MIT          |
| [OSRM](https://project-osrm.org/)                        | BSD-2        |
| [Nominatim](https://nominatim.openstreetmap.org)         | ODbL         |
| [Wikivoyage](https://www.wikivoyage.org/)                | CC BY-SA 3.0 |
| [Waymarked Trails](https://waymarkedtrails.org/)         | ODbL         |
| [Open-Meteo](https://open-meteo.com/)                    | CC BY 4.0    |
| Map Tiles: OpenStreetMap / OpenTopoMap                   | ODbL         |
