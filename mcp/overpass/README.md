# overpass-mcp

MCP server for POI search along cycling routes via the [Overpass API](https://overpass-api.de/) (OpenStreetMap). No API key required.

## Tools

| Tool                      | Description                                  |
| ------------------------- | -------------------------------------------- |
| `search_pois_along_route` | Find POIs within a buffer around a GPX track |

## POI Categories

`beer_garden`, `cafe`, `restaurant`, `swimming`, `bicycle_repair`, `drinking_water`, `viewpoint`, `museum`, `artwork`, `gallery`, `castle`, `memorial`, `ruins`, `church`, `picnic`

### Presets

| Preset                | Categories                                         |
| --------------------- | -------------------------------------------------- |
| `einkehr`             | beer_garden, cafe, restaurant                      |
| `badestellen`         | swimming                                           |
| `sehenswuerdigkeiten` | museum, castle, memorial, ruins, church, viewpoint |
| `kunst`               | artwork, gallery                                   |
| `radservice`          | bicycle_repair, drinking_water                     |
| `rast`                | picnic, drinking_water, viewpoint                  |

## Setup

```json
{
  "overpass": {
    "command": "uv",
    "args": ["run", "--directory", "mcp/overpass", "python", "server.py"]
  }
}
```

## How It Works

1. Reads the GPX track and samples ~80 points along the route
2. Builds an Overpass QL query using the `around` filter with the sampled polyline
3. Queries the Overpass API for matching OSM nodes/ways/relations
4. Returns deduplicated results with name, type, coordinates, and available details

## Tests

```bash
uv run --directory mcp/overpass pytest -v
```
