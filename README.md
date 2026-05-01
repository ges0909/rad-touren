# 🚲 Radtouren Berlin/Brandenburg

Radtouren-Planung für Tagestouren im Raum Berlin/Brandenburg — generiert mit [Kiro](https://kiro.dev), OpenRouteService und VBB-Nahverkehrsdaten.

**→ [Tourenkatalog ansehen](touren.md)**

## Projektstruktur

```
├── touren.md             # Tourenkatalog mit Kartenvorschau
├── *.md                  # Einzelne Tourbeschreibungen (deutsch)
├── gpx/                  # GPX-Dateien für Garmin, Wahoo, Komoot, Strava
├── img/                  # Routenkarten als PNG
├── data/generated_routes/# Rohdaten vom Routing-API (GPX, HTML, PNG)
└── .kiro/
    ├── hooks/            # Agent-Hooks (z.B. GPX-Validierung)
    ├── settings/         # MCP-Server-Konfiguration
    └── steering/         # KI-Steuerungsdokumente
```

## GPX-Dateien verwenden

Die GPX-Dateien im `gpx/`-Ordner können direkt importiert werden in:

- **[gpx.studio](https://gpx.studio/app)** — Visualisierung und Bearbeitung im Browser
- **[brouter-web](https://brouter.de/brouter-web/)** — Routenoptimierung
- **Garmin Connect** / **Wahoo ELEMNT** / **Komoot** / **Strava** — auf Gerät übertragen

## Setup

### Voraussetzungen

- [Kiro IDE](https://kiro.dev)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python-Paketmanager für MCP-Server)
- Node.js / npm (für Weather- und Transport-MCP-Server)

### MCP-Server konfigurieren

1. Kopiere die Vorlage:

   ```bash
   cp .kiro/settings/mcp.json.example .kiro/settings/mcp.json
   ```

2. Trage deinen [OpenRouteService API-Key](https://openrouteservice.org/dev/#/signup) ein:

   ```json
   "OPENROUTESERVICE_API_KEY": "<DEIN_KEY>"
   ```

3. Kiro startet die MCP-Server automatisch.

### Verwendete MCP-Server

| Server                                                                       | Zweck                            | API-Key nötig?    |
| ---------------------------------------------------------------------------- | -------------------------------- | ----------------- |
| [openroute-mcp](https://pypi.org/project/openroute-mcp/)                     | Fahrrad-Routing, GPX-Generierung | ✅ Ja (kostenlos) |
| [open-meteo-mcp-server](https://www.npmjs.com/package/open-meteo-mcp-server) | Wettervorhersage                 | ❌ Nein           |
| [berlin-transport](https://berlin-transport.mcp-tools.app)                   | VBB-Nahverkehr (S-Bahn, RE, Bus) | ❌ Nein           |

## Neue Tour erstellen

Einfach Kiro fragen, z.B.:

> _„Plane eine Radtour von ca. 50 km als Rundkurs ab Potsdam für nächsten Samstag"_

Kiro wird automatisch:

1. Route berechnen und GPX generieren
2. Wetter abfragen
3. Nahverkehrsverbindungen ab Blankenfelde-Mahlow prüfen
4. Sehenswürdigkeiten, Badestellen und Cafés entlang der Route finden
5. Tourbeschreibung als Markdown mit Kartenbild erstellen

## Lizenz

Routendaten: © [OpenRouteService](https://openrouteservice.org/) / [OpenStreetMap](https://www.openstreetmap.org/copyright) Contributors
