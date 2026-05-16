# Travel Content MCP Server

MCP server for extracting structured travel recommendations from blogs and YouTube videos. Uses [Tavily](https://tavily.com/) for search and content extraction. Requires `TAVILY_API_KEY`.

## Tools

| Tool                   | Description                                                    |
| ---------------------- | -------------------------------------------------------------- |
| `search_travel_blogs`  | Search curated travel blogs for route tips and recommendations |
| `search_travel_videos` | Find YouTube travel vlogs and extract transcript highlights    |
| `extract_route_tips`   | Deep-extract structured tips from a specific blog post URL     |

## How It Works

### Blog Search

1. Builds a domain-filtered search query using curated travel blog sources
2. Searches via Tavily with `advanced` depth for full content extraction
3. Returns AI summary + individual blog posts with relevant excerpts

Curated sources include: radtouren.de, bikepacking.com, komoot.de, travelontoast.de, bravebird.de, off-the-path.com, and region-specific sites (spain.info, italien.de, visitnorway.de, etc.)

### Video Search

1. Searches YouTube via Tavily for travel vlogs matching the query
2. Attempts to fetch video transcripts for content extraction
3. Returns video titles, descriptions, and transcript excerpts when available

### Content Extraction

`extract_route_tips` fetches the full text of a blog post for detailed analysis. Use after `search_travel_blogs` to dive deeper into a promising result.

## Setup

1. Ensure `TAVILY_API_KEY` is set in `.env`
2. Install dependencies:

   ```bash
   cd mcp/travel-content
   uv sync
   ```

3. Add to `.kiro/settings/mcp.json`:

   ```json
   {
     "travel-content": {
       "command": "uv",
       "args": [
         "run",
         "--directory",
         "mcp/travel-content",
         "python",
         "server.py"
       ]
     }
   }
   ```

## Usage Examples

Search for cycling blog posts:

```
search_travel_blogs("Spreewald Radtour Tipps", region="brandenburg", activity="cycling")
```

Search for road trip videos:

```
search_travel_videos("Sardinia coastal road trip")
```

Extract tips from a specific blog post:

```
extract_route_tips("https://example.com/blog/nordspanien-roadtrip")
```

## Supported Regions

spain, italy, france, scandinavia, cycling_de (Germany), cycling_eu (Europe-wide), roadtrip_eu

Custom regions work too — the domain filter is a bonus, not a requirement. Tavily searches the full web regardless.
