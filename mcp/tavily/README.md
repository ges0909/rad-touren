# Tavily MCP Server

MCP server for web search and content extraction via the [Tavily API](https://tavily.com/). Requires API key.

## Tools

| Tool          | Description                              |
| ------------- | ---------------------------------------- |
| `web_search`  | Search the web for current information   |
| `web_extract` | Extract main content from a specific URL |

## Setup

1. Register at [tavily.com](https://tavily.com/) and get an API key
2. Add to `.env`:

   ```
   TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxx
   ```

3. Install dependencies:

   ```bash
   cd mcp/tavily
   uv sync
   ```

4. Enable in `.kiro/settings/mcp.json`:

   ```json
   {
     "tavily": {
       "command": "uv",
       "args": ["run", "--directory", "mcp/tavily", "python", "server.py"]
     }
   }
   ```

## Usage Examples

Web search:

```
web_search("best cycling routes Brandenburg 2025")
web_search("ferry schedule Sardinia", search_depth="advanced")
```

Extract page content:

```
web_extract("https://example.com/article")
```

## Rate Limits

- Free tier: 1,000 searches/month
- No credit card required for free tier
