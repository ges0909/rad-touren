# BRouter MCP Server

Ein Python MCP-Server, der die [BRouter](https://brouter.de) Fahrrad-Routing-API und die [Nominatim](https://nominatim.openstreetmap.org) Geocoding-API als MCP-Tools bereitstellt. Gebaut mit [FastMCP](https://github.com/jlowin/fastmcp).

BRouter ist spezialisiert auf Fahrrad-Routing: es folgt Fernradwegen, ist tolerant beim Waypoint-Snapping und berücksichtigt Höhenprofile. Kein API-Key nötig. Zusätzlich kann der Server GPX-Tracks als Kartenbilder (PNG) mit OpenStreetMap-Hintergrund rendern.

## Tools

### `calculate_route`

Berechnet eine Fahrradroute über Wegpunkte.

| Parameter        | Typ                 | Pflicht | Default      | Beschreibung                                                  |
| ---------------- | ------------------- | ------- | ------------ | ------------------------------------------------------------- |
| `waypoints`      | `list[list[float]]` | Ja      | —            | Koordinatenpaare als `[Längengrad, Breitengrad]` (mind. 2)    |
| `profile`        | `str`               | Nein    | `"trekking"` | Routing-Profil (siehe unten)                                  |
| `format`         | `str`               | Nein    | `"gpx"`      | Ausgabeformat: `"gpx"` oder `"geojson"`                       |
| `alternativeidx` | `int`               | Nein    | `0`          | Alternativrouten-Index (0–3)                                  |
| `nogos`          | `list[dict]`        | Nein    | `None`       | Sperrzonen: `[{"lon": float, "lat": float, "radius": float}]` |
| `track_name`     | `str`               | Nein    | `None`       | Name für das GPX `<trk><name>`-Element                        |

**Verfügbare Profile:** `trekking`, `fastbike`, `trekking-ignore-cr`, `safety`, `shortest`, `trekking-steep`, `trekking-noferries`, `trekking-nosteps`

**Rückgabe:** Routenzusammenfassung (Distanz, Höhenmeter, geschätzte Dauer) + GPX- oder GeoJSON-Daten.

### `search_location`

Sucht Orte per Name über die Nominatim-API.

| Parameter      | Typ   | Pflicht | Default | Beschreibung                         |
| -------------- | ----- | ------- | ------- | ------------------------------------ |
| `query`        | `str` | Ja      | —       | Suchbegriff (Ortsname, Adresse etc.) |
| `country_code` | `str` | Nein    | `"de"`  | ISO 3166-1 Alpha-2 Ländercode        |
| `limit`        | `int` | Nein    | `5`     | Maximale Anzahl Ergebnisse (1–40)    |

**Rückgabe:** Nummerierte Ergebnisse mit Name, Koordinaten als `[Längengrad, Breitengrad]` und Adresse.

### `render_gpx_map`

Rendert einen GPX-Track als PNG-Kartenbild mit OpenStreetMap-Kacheln.

| Parameter     | Typ   | Pflicht | Default     | Beschreibung                 |
| ------------- | ----- | ------- | ----------- | ---------------------------- |
| `gpx_path`    | `str` | Ja      | —           | Pfad zur GPX-Datei           |
| `output_path` | `str` | Ja      | —           | Pfad für das PNG-Ausgabebild |
| `width`       | `int` | Nein    | `800`       | Bildbreite in Pixeln         |
| `height`      | `int` | Nein    | `600`       | Bildhöhe in Pixeln           |
| `line_color`  | `str` | Nein    | `"#0066CC"` | Linienfarbe als Hex-String   |
| `line_width`  | `int` | Nein    | `3`         | Linienbreite in Pixeln       |

**Hinweis:** Pfade werden relativ zum Arbeitsverzeichnis des MCP-Servers aufgelöst. Bei Kiro-Konfiguration mit `--directory brouter-mcp` absolute Pfade verwenden.

**Rückgabe:** Erfolgsmeldung mit Dateipfad, Bildgröße und Anzahl der Trackpoints.

## Voraussetzungen

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python-Paketmanager)

## Installation

```bash
cd brouter-mcp
uv sync
```

## Server starten (standalone)

```bash
cd brouter-mcp
uv run python server.py
```

## Kiro MCP-Konfiguration

In `.kiro/settings/mcp.json` folgenden Eintrag hinzufügen:

```json
{
  "mcpServers": {
    "brouter": {
      "command": "uv",
      "args": ["run", "--directory", "brouter-mcp", "python", "server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Der `--directory`-Pfad ist relativ zum Workspace-Root. Nach dem Speichern der Konfiguration verbindet sich Kiro automatisch mit dem Server.

## Tests

```bash
cd brouter-mcp
uv run pytest -v
```

Die Testsuite umfasst:

- **Property-Based Tests** (Hypothesis) — Validierung, URL-Konstruktion, GPX-Parsing, Koordinatentransformation
- **Unit Tests** — Defaults, Randfälle, Fehlerbehandlung
- **Integrationstests** (respx) — Gemockte HTTP-Aufrufe für beide APIs
- **Render-Tests** — GPX-zu-PNG-Rendering, Fehlerbehandlung, Dateierzeugung

## Projektstruktur

```
brouter-mcp/
├── server.py          # MCP-Server (Single-File)
├── pyproject.toml     # Paketdefinition und Abhängigkeiten
└── tests/
    ├── test_server.py        # Property-Based und Unit Tests
    ├── test_integration.py   # Integrationstests mit HTTP-Mocks
    └── test_render_gpx_map.py # Tests für GPX-zu-PNG-Rendering
```
