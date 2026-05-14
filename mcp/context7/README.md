# Context7 MCP Server (Python)

Up-to-date library documentation for LLMs via the [Context7](https://context7.com) API.

## Features

- **resolve_library_id** — Search for a library by name, get Context7 IDs
- **get_library_docs** — Fetch current documentation for a specific query

## Setup

```bash
cd mcp/context7
uv sync
```

Add your API key to `.env`:

```bash
CONTEXT7_API_KEY=ctx7sk-your-key-here
```

Get a free key at [context7.com](https://context7.com).

## Usage

```bash
fastmcp run server.py
```

## Example

```
> resolve_library_id("fastapi", "dependency injection")
→ /tiangolo/fastapi (ID)

> get_library_docs("/tiangolo/fastapi", "How to use Depends for dependency injection")
→ Current documentation with code examples
```

## Why Python?

This replaces the Node.js-based `@upstash/context7-mcp` package, keeping the entire MCP stack in Python (consistent with all other servers in this project). Same API, no `npx` dependency.
