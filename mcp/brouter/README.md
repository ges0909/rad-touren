# BRouter MCP Server

A Python MCP server exposing the [BRouter](https://brouter.de) cycling routing API and [Nominatim](https://nominatim.openstreetmap.org) geocoding API as MCP tools. Built with [FastMCP](https://github.com/jlowin/fastmcp).

BRouter specializes in bicycle routing: it follows long-distance cycle routes, is tolerant with waypoint snapping, and considers elevation profiles. No API key required. The server can also render GPX tracks as map images (PNG) with OpenStreetMap tiles and generate elevation profile charts.

## Tools

### `calculate_route`

Calculate a cycling route through waypoints.

| Parameter        | Type                | Required | Default      | Description                                                    |
| ---------------- | ------------------- | -------- | ------------ | -------------------------------------------------------------- |
| `waypoints`      | `list[list[float]]` | Yes      | —            | Coordinate pairs as `[longitude, latitude]` (min 2)            |
| `profile`        | `str`               | No       | `"trekking"` | Routing profile (see below)                                    |
| `format`         | `str`               | No       | `"gpx"`      | Output format: `"gpx"` or `"geojson"`                          |
| `alternativeidx` | `int`               | No       | `0`          | Alternative route index (0–3)                                  |
| `nogos`          | `list[dict]`        | No       | `None`       | No-go areas: `[{"lon": float, "lat": float, "radius": float}]` |
| `track_name`     | `str`               | No       | `None`       | Name for the GPX `<trk><name>` element                         |

**Available profiles:** `trekking`, `fastbike`, `trekking-ignore-cr`, `safety`, `shortest`, `trekking-steep`, `trekking-noferries`, `trekking-nosteps`

**Returns:** JSON with route summary (distance, elevation gain, estimated duration, geometry) + GPX data, or GeoJSON block.

### `search_location`

Search for locations by name via the Nominatim API.

| Parameter      | Type  | Required | Default | Description                              |
| -------------- | ----- | -------- | ------- | ---------------------------------------- |
| `query`        | `str` | Yes      | —       | Search query (place name, address, etc.) |
| `country_code` | `str` | No       | `"de"`  | ISO 3166-1 alpha-2 country code          |
| `limit`        | `int` | No       | `5`     | Maximum number of results (1–40)         |

**Returns:** Numbered results with name, coordinates as `[longitude, latitude]`, and address.

### `render_gpx_map`

Render a GPX track as a PNG map image with OpenStreetMap tiles. Optionally displays POIs as colored markers on the map.

| Parameter     | Type         | Required | Default     | Description                   |
| ------------- | ------------ | -------- | ----------- | ----------------------------- |
| `gpx_path`    | `str`        | Yes      | —           | Path to the GPX file          |
| `output_path` | `str`        | Yes      | —           | Path for the PNG output image |
| `width`       | `int`        | No       | `800`       | Image width in pixels         |
| `height`      | `int`        | No       | `600`       | Image height in pixels        |
| `line_color`  | `str`        | No       | `"#0066CC"` | Line color as hex string      |
| `line_width`  | `int`        | No       | `3`         | Line width in pixels          |
| `pois`        | `list[dict]` | No       | `None`      | POI markers (see below)       |

**POI format:** Each entry is a dict with:

- `lat` (float, required) — latitude
- `lon` (float, required) — longitude
- `category` (str, optional) — category for color coding
- `name` (str, optional) — POI name

**Available categories:** `museum`, `castle`, `memorial`, `ruins`, `church`, `viewpoint`, `artwork`, `gallery`, `beer_garden`, `cafe`, `restaurant`, `swimming`, `bicycle_repair`, `drinking_water`, `picnic`

When POIs are present, a legend is automatically rendered (sights, art, food, swimming).

**Returns:** Success message with file path, image size, trackpoint count, and POI marker count.

### `render_elevation_profile`

Render an elevation profile chart from a GPX track as a PNG image.

| Parameter     | Type  | Required | Default | Description                   |
| ------------- | ----- | -------- | ------- | ----------------------------- |
| `gpx_path`    | `str` | Yes      | —       | Path to the GPX file          |
| `output_path` | `str` | Yes      | —       | Path for the PNG output image |
| `width`       | `int` | No       | `800`   | Image width in pixels         |
| `height`      | `int` | No       | `300`   | Image height in pixels        |

**Returns:** Success message with stats: total distance, elevation range, ascent and descent.

## Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)

## Installation

```bash
cd mcp/brouter
uv sync
```

## Running standalone

```bash
cd mcp/brouter
uv run python server.py
```

## Kiro MCP configuration

Add the following entry to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "brouter": {
      "command": "uv",
      "args": ["run", "--directory", "mcp/brouter", "python", "server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

The `--directory` path is relative to the workspace root. Kiro reconnects automatically after saving the config.

**Note:** File paths in `render_gpx_map` and `render_elevation_profile` are resolved relative to the MCP server's working directory. Use absolute paths when configured with `--directory`.

## Tests

```bash
cd mcp/brouter
uv run pytest -v
```

The test suite includes:

- **Property-based tests** (Hypothesis) — validation, URL construction, GPX parsing, coordinate transformation
- **Unit tests** — defaults, edge cases, error handling
- **Integration tests** (respx) — mocked HTTP calls for both APIs
- **Render tests** — GPX-to-PNG rendering (map + elevation profile), POI markers, legend, error handling

## Project structure

```
mcp/brouter/
├── brouter.py         # BRouter and Nominatim client library
├── server.py          # MCP server with all tools
├── icons/             # Twemoji-based POI markers (CC-BY 4.0)
├── pyproject.toml     # Package definition and dependencies
└── tests/
    ├── test_server.py                # Property-based and unit tests
    ├── test_integration.py           # Integration tests with HTTP mocks
    ├── test_render_gpx_map.py        # Map rendering + POI tests
    └── test_render_elevation_profile.py  # Elevation profile tests
```
