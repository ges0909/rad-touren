# Design Document

## Overview

This design replaces the static tool registry in `app/backend/tools.py` with a dynamic MCP subprocess manager. Instead of importing `lib.*` modules directly, the backend spawns MCP servers as subprocesses using stdio JSON-RPC transport and discovers tools dynamically via `tools/list`. This eliminates the need for `tools.py`, the shared `lib/` package, and the steering sanitization logic.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  app/backend/                                                │
│                                                              │
│  main.py ──► agent.py ──► mcp_manager.py                    │
│                │                 │                            │
│                │           ┌─────┴──────────────┐            │
│                │           │  Server Registry    │            │
│                │           │  (lazy subprocess   │            │
│                │           │   pool)             │            │
│                │           └─────┬──────────────┘            │
│                │                 │ stdio JSON-RPC             │
│                ▼                 ▼                            │
│           SSE events      ┌───────────┐                      │
│           (map, tour,     │ mcp/      │                      │
│            status, done)  │ brouter/  │ ← self-contained     │
│                           │ ors/      │   FastMCP servers     │
│                           │ osrm/     │                      │
│                           │ ...       │                      │
│                           └───────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. MCP Manager Module (`app/backend/mcp_manager.py`)

Central module responsible for subprocess lifecycle, tool discovery, and call routing.

```python
"""MCP subprocess manager — lazy spawn, tool discovery, call routing."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project root (two levels up from app/backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""

    name: str
    prefix: str  # e.g. "brouter", "open_meteo"
    command: list[str]  # e.g. ["uv", "run", "python", "server.py"]
    cwd: Path  # working directory


@dataclass
class ServerInstance:
    """A running MCP server subprocess."""

    config: ServerConfig
    process: asyncio.subprocess.Process
    request_id: int = 0
    tools: list[dict[str, Any]] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def next_id(self) -> int:
        self.request_id += 1
        return self.request_id


# Server name mappings: directory name → tool prefix
SERVER_PREFIX_MAP: dict[str, str] = {
    "brouter": "brouter",
    "open-meteo": "open_meteo",
    "vbb": "vbb",
    "overpass": "overpass",
    "ors": "openrouteservice",
    "osrm": "osrm",
    "wikivoyage": "wikivoyage",
    "waymarkedtrails": "waymarkedtrails",
}


class MCPManager:
    """Manages MCP server subprocesses with lazy startup and tool discovery."""

    def __init__(self, configs: list[ServerConfig]) -> None:
        self._configs: dict[str, ServerConfig] = {c.name: c for c in configs}
        self._instances: dict[str, ServerInstance] = {}
        self._tool_map: dict[str, tuple[str, str]] = {}  # prefixed_name → (server_name, original_name)
        self._declarations: list[dict[str, Any]] = []

    async def get_tool_declarations(self) -> list[dict[str, Any]]:
        """Return combined Gemini-compatible tool declarations from all servers."""
        ...

    async def call_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a tool call to the correct MCP server."""
        ...

    async def shutdown(self) -> None:
        """Terminate all running subprocesses."""
        ...

    async def _ensure_server(self, server_name: str) -> ServerInstance:
        """Spawn server if not running, return instance."""
        ...

    async def _spawn_server(self, config: ServerConfig) -> ServerInstance:
        """Spawn subprocess, perform initialize handshake, discover tools."""
        ...

    async def _send_request(self, instance: ServerInstance, method: str, params: dict) -> Any:
        """Send JSON-RPC request and read response."""
        ...
```

### 2. Server Configuration (`app/backend/mcp_manager.py`)

Server configs are defined as a constant list within the module. Each entry maps a server identifier to its launch command and working directory.

```python
def build_server_configs() -> list[ServerConfig]:
    """Build server configurations for all 8 tour-planning MCP servers."""
    servers = [
        ("brouter", "mcp/brouter"),
        ("open-meteo", "mcp/open-meteo"),
        ("vbb", "mcp/vbb"),
        ("overpass", "mcp/overpass"),
        ("ors", "mcp/ors"),
        ("osrm", "mcp/osrm"),
        ("wikivoyage", "mcp/wikivoyage"),
        ("waymarkedtrails", "mcp/waymarkedtrails"),
    ]
    configs: list[ServerConfig] = []
    for name, directory in servers:
        configs.append(
            ServerConfig(
                name=name,
                prefix=SERVER_PREFIX_MAP[name],
                command=["uv", "run", "--directory", str(PROJECT_ROOT / directory), "python", "server.py"],
                cwd=PROJECT_ROOT / directory,
            )
        )
    return configs
```

### 3. Subprocess Lifecycle

#### Lazy Spawn

Servers are only spawned when a tool belonging to that server is first called. The `_ensure_server` method checks if an instance exists and is alive, spawning if needed.

```python
async def _ensure_server(self, server_name: str) -> ServerInstance:
    """Ensure server is running. Spawn if not started or if process died."""
    instance = self._instances.get(server_name)
    if instance and instance.process.returncode is None:
        return instance

    # Process died or never started — (re)spawn
    config = self._configs[server_name]
    logger.info("Spawning MCP server: %s", server_name)
    instance = await self._spawn_server(config)
    self._instances[server_name] = instance
    return instance
```

#### Spawn + Initialize + Discover

```python
async def _spawn_server(self, config: ServerConfig) -> ServerInstance:
    """Spawn subprocess, send initialize, call tools/list."""
    process = await asyncio.create_subprocess_exec(
        *config.command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=config.cwd,
        env=None,  # inherit current process environment (os.environ)
    )

    instance = ServerInstance(config=config, process=process)

    # MCP initialize handshake
    await self._send_request(instance, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "trip-planner-backend", "version": "0.1.0"},
    })

    # Send initialized notification
    await self._send_notification(instance, "notifications/initialized", {})

    # Discover tools
    result = await self._send_request(instance, "tools/list", {})
    instance.tools = result.get("tools", [])

    # Register tools in the global map
    for tool in instance.tools:
        original_name = tool["name"]
        prefixed = f"mcp_{config.prefix}_{original_name}".replace("-", "_")
        self._tool_map[prefixed] = (config.name, original_name)

    logger.info("Server %s ready: %d tools", config.name, len(instance.tools))
    return instance
```

#### Shutdown

```python
async def shutdown(self) -> None:
    """Terminate all running MCP server subprocesses."""
    for name, instance in self._instances.items():
        if instance.process.returncode is None:
            instance.process.terminate()
            try:
                await asyncio.wait_for(instance.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                instance.process.kill()
            logger.info("Terminated MCP server: %s", name)
    self._instances.clear()
```

#### Respawn on Crash

Built into `_ensure_server` — if `process.returncode is not None`, the server is respawned transparently on the next tool call.

### 4. JSON-RPC Communication

```python
async def _send_request(self, instance: ServerInstance, method: str, params: dict) -> Any:
    """Send JSON-RPC 2.0 request over stdin, read response from stdout."""
    request_id = await instance.next_id()
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }

    payload = json.dumps(request) + "\n"
    instance.process.stdin.write(payload.encode())
    await instance.process.stdin.drain()

    # Read response line (newline-delimited JSON)
    line = await asyncio.wait_for(
        instance.process.stdout.readline(),
        timeout=60.0,
    )

    response = json.loads(line)
    if "error" in response:
        return {"error": response["error"].get("message", "Unknown MCP error")}
    return response.get("result", {})


async def _send_notification(self, instance: ServerInstance, method: str, params: dict) -> None:
    """Send a JSON-RPC notification (no response expected)."""
    notification = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
    }
    payload = json.dumps(notification) + "\n"
    instance.process.stdin.write(payload.encode())
    await instance.process.stdin.drain()
```

### 5. Tool Discovery and Schema Conversion

MCP tool schemas are converted to Gemini `FunctionDeclaration` format:

```python
def _mcp_schema_to_gemini(self, tool: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Convert an MCP tool schema to a Gemini FunctionDeclaration dict.

    MCP schema format:
        {"name": "calculate_route", "description": "...", "inputSchema": {"type": "object", "properties": {...}, "required": [...]}}

    Gemini format:
        {"name": "mcp_brouter_calculate_route", "description": "...", "parameters": {"type": "object", "properties": {...}, "required": [...]}}
    """
    original_name = tool["name"]
    prefixed_name = f"mcp_{prefix}_{original_name}".replace("-", "_")

    declaration: dict[str, Any] = {
        "name": prefixed_name,
        "description": tool.get("description", ""),
    }

    input_schema = tool.get("inputSchema", {})
    if input_schema:
        # Gemini uses "parameters" key with the same JSON Schema structure
        declaration["parameters"] = {
            "type": input_schema.get("type", "object"),
            "properties": input_schema.get("properties", {}),
        }
        required = input_schema.get("required")
        if required:
            declaration["parameters"]["required"] = required

    return declaration
```

### 6. Tool Dispatch Routing

```python
async def call_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Route a tool call to the correct MCP server subprocess.

    Args:
        prefixed_name: Full tool name (e.g. "mcp_brouter_calculate_route").
        arguments: Tool arguments as a dict.

    Returns:
        Tool result as a dict, or {"error": "..."} on failure.
    """
    mapping = self._tool_map.get(prefixed_name)
    if not mapping:
        return {"error": f"Unknown tool: {prefixed_name}"}

    server_name, original_name = mapping

    try:
        instance = await self._ensure_server(server_name)
    except Exception as e:
        logger.error("Failed to start server %s: %s", server_name, e)
        return {"error": f"Server {server_name} unavailable: {e}"}

    try:
        result = await self._send_request(instance, "tools/call", {
            "name": original_name,
            "arguments": arguments,
        })
    except asyncio.TimeoutError:
        logger.error("Tool %s timed out (60s)", prefixed_name)
        return {"error": f"Tool {prefixed_name} timed out after 60 seconds"}
    except Exception as e:
        logger.error("Tool %s failed: %s", prefixed_name, e)
        return {"error": str(e)}

    # MCP tools/call returns {"content": [{"type": "text", "text": "..."}]}
    # Extract text content and parse as JSON if possible
    content = result.get("content", [])
    if content and isinstance(content, list):
        text_parts = [c["text"] for c in content if c.get("type") == "text"]
        combined = "\n".join(text_parts)
        try:
            return json.loads(combined)
        except (json.JSONDecodeError, ValueError):
            return {"text": combined}

    return result
```

### 7. Integration with `agent.py`

The agent loop changes from importing `TOOL_DECLARATIONS` and `TOOL_REGISTRY` to using the `MCPManager` instance:

```python
# Before (tools.py imports):
from tools import TOOL_DECLARATIONS, TOOL_REGISTRY

# After (mcp_manager):
from mcp_manager import MCPManager

async def run_agent(
    client: genai.Client,
    user_message: str,
    chat_history: list[dict[str, str]],
    mcp: MCPManager,  # new parameter
    language: str = "de",
) -> AsyncGenerator[SSEEvent, None]:
    # Get declarations dynamically
    declarations = await mcp.get_tool_declarations()

    tools = types.Tool(
        function_declarations=[types.FunctionDeclaration(**decl) for decl in declarations]
    )

    # ... in the tool execution section:
    result = await mcp.call_tool(tool_name, tool_args)
```

#### Lifecycle in `main.py`

```python
from contextlib import asynccontextmanager
from mcp_manager import MCPManager, build_server_configs

_mcp_manager: MCPManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and shutdown MCP manager."""
    global _mcp_manager
    configs = build_server_configs()
    _mcp_manager = MCPManager(configs)
    # Pre-discover tools from all servers (optional: can also be lazy)
    await _mcp_manager.discover_all_tools()
    yield
    await _mcp_manager.shutdown()


app = FastAPI(title="Trip Planner API", lifespan=lifespan)
```

### 8. Geo Data Event Emission Strategy

The current `agent.py` emits `map` SSE events by inspecting tool names and response shapes. After migration, tool names use `mcp_` prefixes, so the pattern matching adapts:

```python
# Geo-relevant tool detection by name pattern
GEO_ROUTE_PATTERNS = ("route", "calculate_car", "calculate_bike")
GEO_POINT_PATTERNS = ("geocode", "search_location")


def _is_route_tool(name: str) -> bool:
    """Check if a tool name indicates route geometry in the response."""
    return any(p in name for p in GEO_ROUTE_PATTERNS)


def _is_geocode_tool(name: str) -> bool:
    """Check if a tool name indicates geocoding results."""
    return any(p in name for p in GEO_POINT_PATTERNS)


# In the tool execution loop:
if _is_route_tool(tool_name) and isinstance(result, dict):
    geometry = result.get("geometry")
    if geometry:
        yield {"event": "map", "data": {"route": [[lat, lon] for lat, lon in geometry]}}
    # Strip geometry before sending to LLM (context savings)
    result.pop("geometry", None)

elif _is_geocode_tool(tool_name) and isinstance(result, dict):
    results = result.get("results", [])
    if results:
        coords = results[0].get("coordinates", [])
        if len(coords) == 2:
            yield {"event": "map", "data": {"waypoints": [[coords[1], coords[0]]]}}
```

### 9. Steering Module Simplification

After migration, `steering.py` removes:

- `_SECTIONS_TO_STRIP` list
- `_sanitize_steering()` function
- Tool mapping section in the base prompt
- All `mcp_` rewriting logic

The simplified `build_system_prompt` loads steering files directly and builds the tool list from the MCP manager's declarations:

```python
def build_system_prompt(
    tool_names: list[str],
    language: str = "de",
    user_message: str = "",
) -> str:
    """Assemble system prompt. Tool names come from MCP manager."""
    lang_name = "German" if language == "de" else "English"
    tool_list_str = ", ".join(f"`{name}`" for name in tool_names)

    base_prompt = f"""You are a travel planning assistant...

## Available Tools
{tool_list_str}

Respond ONLY in {lang_name}.
"""
    # Load steering files (no sanitization needed)
    parts = [base_prompt]
    for filename in _select_files(user_message):
        path = STEERING_DIR / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            parts.append(content)

    return "\n\n---\n\n".join(parts)
```

### 10. Migration Plan

The migration proceeds in phases to keep the app functional at each step:

| Phase | Action                                                                           | Validates |
| ----- | -------------------------------------------------------------------------------- | --------- |
| 1     | Create `mcp_manager.py` with subprocess lifecycle + JSON-RPC                     | Req 1, 3  |
| 2     | Add tool discovery + schema conversion                                           | Req 2, 4  |
| 3     | Wire `MCPManager` into `agent.py` alongside existing `TOOL_REGISTRY` (dual mode) | Req 9     |
| 4     | Inline `lib/` modules into each MCP server, remove workspace dep                 | Req 7     |
| 5     | Remove `tools.py` static registry, switch agent to MCP-only                      | Req 5     |
| 6     | Remove steering sanitization                                                     | Req 6     |
| 7     | Delete `lib/` directory, clean up `pyproject.toml`                               | Req 7     |

#### Dual-Mode Transition (Phase 3)

During migration, both registries coexist:

```python
# agent.py during transition
result = await mcp.call_tool(tool_name, tool_args)
if "error" in result and result["error"].startswith("Unknown tool"):
    # Fallback to legacy registry
    tool_fn = TOOL_REGISTRY.get(tool_name)
    if tool_fn:
        result = await tool_fn(**tool_args)
```

## Data Models

### ServerConfig

| Field     | Type        | Description                                        |
| --------- | ----------- | -------------------------------------------------- |
| `name`    | `str`       | Server identifier (directory name, e.g. "brouter") |
| `prefix`  | `str`       | Tool name prefix (e.g. "brouter", "open_meteo")    |
| `command` | `list[str]` | Subprocess launch command                          |
| `cwd`     | `Path`      | Working directory for the subprocess               |

### ServerInstance

| Field        | Type                         | Description                            |
| ------------ | ---------------------------- | -------------------------------------- |
| `config`     | `ServerConfig`               | Reference to server configuration      |
| `process`    | `asyncio.subprocess.Process` | Running subprocess handle              |
| `request_id` | `int`                        | Auto-incrementing JSON-RPC request ID  |
| `tools`      | `list[dict]`                 | Raw MCP tool schemas from `tools/list` |

### Tool Map Entry

| Key                                 | Value                                | Example                    |
| ----------------------------------- | ------------------------------------ | -------------------------- |
| `"mcp_brouter_calculate_route"`     | `("brouter", "calculate_route")`     | Route to brouter server    |
| `"mcp_openrouteservice_geocode"`    | `("ors", "geocode")`                 | Route to ORS server        |
| `"mcp_open_meteo_weather_forecast"` | `("open-meteo", "weather_forecast")` | Route to open-meteo server |

## Error Handling

| Scenario                     | Behavior                                                      |
| ---------------------------- | ------------------------------------------------------------- |
| Server fails to spawn        | Return `{"error": "Server X unavailable: ..."}` to agent loop |
| Server crashes mid-session   | Next call triggers respawn via `_ensure_server`               |
| Tool call times out (>60s)   | Return `{"error": "Tool X timed out after 60 seconds"}`       |
| JSON-RPC error response      | Return `{"error": "<message from server>"}`                   |
| Unknown tool name            | Return `{"error": "Unknown tool: X"}`                         |
| All servers down at shutdown | `terminate()` + `kill()` after 5s timeout                     |

## Testing Strategy

- **Unit tests**: Verify schema conversion, name mapping, geo-event detection with concrete examples.
- **Property tests**: Validate universal invariants (lifecycle, routing, round-trips) using Hypothesis with mocked subprocesses.
- **Integration tests**: Verify actual subprocess spawn/shutdown and JSON-RPC communication with a real MCP server (e.g. the simplest one like `open-meteo`).
- **Smoke tests**: Verify migration completeness (no `lib.*` imports, no `_sanitize_steering`, no `TOOL_REGISTRY`).

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Subprocess Lifecycle — Lazy Spawn and Reuse

_For any_ sequence of tool calls targeting the same MCP server, the first call SHALL trigger exactly one subprocess spawn, and all subsequent calls SHALL reuse that same subprocess (no additional spawns occur while the process is alive).

**Validates: Requirements 1.1, 1.2**

### Property 2: Subprocess Respawn After Crash

_For any_ MCP server whose subprocess has exited unexpectedly (returncode is not None), the next tool call targeting that server SHALL spawn a new subprocess and complete successfully.

**Validates: Requirements 1.4**

### Property 3: Schema Conversion Correctness

_For any_ valid MCP tool schema with a name, description, and inputSchema, converting it to a Gemini FunctionDeclaration SHALL produce a dict with: (a) name matching `mcp_<prefix>_<original_name>` with all hyphens replaced by underscores, (b) the original description preserved, and (c) parameters matching the inputSchema structure (type, properties, required).

**Validates: Requirements 2.2, 4.1, 4.3**

### Property 4: Combined Declarations Aggregation

_For any_ set of N configured MCP servers each exposing M_i tools, the combined tool declarations list SHALL contain exactly sum(M_i) entries, each with a unique prefixed name.

**Validates: Requirements 2.3**

### Property 5: Tool Routing Correctness

_For any_ registered tool with prefixed name `mcp_<prefix>_<tool>`, calling `call_tool` with that name SHALL route the invocation to the MCP server whose prefix matches, using the original (unprefixed) tool name in the `tools/call` JSON-RPC request.

**Validates: Requirements 2.4, 3.1**

### Property 6: Argument Serialization Round-Trip

_For any_ valid tool arguments dict (containing strings, numbers, booleans, lists, and nested dicts), serializing to JSON-RPC and deserializing the response SHALL preserve data types and values without loss.

**Validates: Requirements 3.2**

### Property 7: Error Response Propagation

_For any_ JSON-RPC error response from an MCP server (with varying error codes and messages), the MCPManager SHALL return a dict containing an "error" key whose value includes the original error message text.

**Validates: Requirements 3.4**

### Property 8: Steering Passthrough

_For any_ steering file content containing `mcp_` prefixed tool names, loading the content through the simplified steering module SHALL preserve all `mcp_` prefixed names unchanged in the output.

**Validates: Requirements 6.1**

### Property 9: Geo-Event Emission

_For any_ tool response from a geo-relevant tool (name matching route/geocode/search_location patterns) that contains geometry or coordinate data, the agent loop SHALL emit a `map` SSE event with coordinates in `[[lat, lng], ...]` format.

**Validates: Requirements 9.1, 9.2, 9.3**
