# Travel Content MCP Server

MCP server for finding travel journalism and route tips from quality media sources. Uses [Tavily](https://tavily.com/) for search and content extraction. Requires `TAVILY_API_KEY`.

## Tools

| Tool                     | Description                                                             |
| ------------------------ | ----------------------------------------------------------------------- |
| `search_travel_articles` | Search quality newspapers and travel magazines for destination tips     |
| `search_travel_videos`   | Find ÖR travel content (WDR, NDR, ARD, BR, SWR) — transcript via Tavily |
| `extract_route_tips`     | Deep-extract structured tips from a specific article URL                |

## Source Philosophy

Content is sourced from **established, trusted media only** — not random travel blogs:

| Category              | Sources                                                        |
| --------------------- | -------------------------------------------------------------- |
| German quality press  | spiegel.de, zeit.de, sueddeutsche.de, faz.net, tagesspiegel.de |
| Travel magazines (DE) | geo.de, merian.de, nationalgeographic.de                       |
| Travel magazines (EN) | lonelyplanet.com, roughguides.com, cntraveler.com              |
| International press   | theguardian.com, bbc.com, nytimes.com                          |
| Public broadcasters   | ndr.de, br.de, swr.de, wdr.de, ardmediathek.de                 |
| Cycling (route data)  | komoot.de, outdooractive.com, adfc.de                          |

Region-specific quality sources (spain.info, elpais.com, etc.) are added when a region is provided.

## How It Works

### Article Search (`search_travel_articles`)

1. Builds a domain-filtered query from the trusted source list above
2. Searches via Tavily with `advanced` depth
3. Returns AI summary + individual articles with relevant excerpts

### Video Search (`search_travel_videos`)

1. Searches YouTube and mediatheks for ÖR broadcaster content
2. Attempts Tavily-based transcript extraction
3. For reliable transcripts use the dedicated `travel-videos` MCP server with `youtube-transcript-api`

### Content Extraction (`extract_route_tips`)

Fetches the full text of a specific article for detailed analysis. Use after `search_travel_articles` to dig deeper into a promising result.

## Setup

1. Ensure `TAVILY_API_KEY` is set in `.env`
2. Install dependencies:

   ```bash
   cd mcp/travel-content
   uv sync
   ```

## Usage Examples

```python
search_travel_articles("Nordspanien Küste Roadtrip Tipps", region="spain", activity="roadtrip")
search_travel_articles("Spreewald Radtour", region="brandenburg", activity="cycling")
search_travel_videos("Baskenland Kantabrien Reisedoku")
extract_route_tips("https://www.geo.de/reisen/nordspanien-roadtrip")
```
