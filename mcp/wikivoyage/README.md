# Wikivoyage MCP Server

MCP server that provides access to [Wikivoyage](https://www.wikivoyage.org/) travel guides via the MediaWiki API. Supports both the German and English editions.

## Tools

| Tool                   | Description                                                          |
| ---------------------- | -------------------------------------------------------------------- |
| `search_destinations`  | Search for travel destinations by name or keyword                    |
| `get_article`          | Retrieve the full travel guide for a destination                     |
| `get_section`          | Extract a specific section (e.g. Anreise, Küche, Sehenswürdigkeiten) |
| `get_article_sections` | List all available sections of an article                            |
| `search_nearby`        | Find Wikivoyage articles near given coordinates                      |

## Setup

```bash
cd mcp/wikivoyage
uv sync
```

## Run

```bash
uv run fastmcp run server.py
```

## Usage Examples

Search for a destination:

```
search_destinations("Spreewald")
search_destinations("San Sebastián", lang="en")
```

Get restaurant recommendations for a city:

```
get_section("Barcelona", "Küche")
```

Find places near a route point:

```
search_nearby(lat=43.32, lon=-1.98, radius=5000)
```

## API Reference

This server uses the [MediaWiki Action API](https://www.mediawiki.org/wiki/API:Action_API) endpoints:

- `de.wikivoyage.org/w/api.php` (German edition)
- `en.wikivoyage.org/w/api.php` (English edition)

All content is licensed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
