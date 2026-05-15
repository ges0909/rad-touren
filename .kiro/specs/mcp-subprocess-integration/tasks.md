# Implementation Plan: MCP Subprocess Integration

## Overview

Replace the static tool registry in `app/backend/tools.py` with a dynamic MCP subprocess manager. The migration proceeds in 7 phases to keep the app functional at each step: create the MCP manager, add tool discovery, wire into agent (dual mode), inline lib modules, remove static registry, remove steering sanitization, and clean up.

## Tasks

- [x] 1. Create MCP Manager with subprocess lifecycle and JSON-RPC
  - [x] 1.1 Create `app/backend/mcp_manager.py` with data models and server configuration
    - Define `ServerConfig` and `ServerInstance` dataclasses
    - Define `SERVER_PREFIX_MAP` constant with all 8 server name mappings
    - Implement `build_server_configs()` to generate configs for all 8 MCP servers
    - _Requirements: 1.5, 8.1, 8.2_

  - [x] 1.2 Implement JSON-RPC communication layer in `mcp_manager.py`
    - Implement `_send_request()` with newline-delimited JSON over stdin/stdout
    - Implement `_send_notification()` for fire-and-forget messages
    - Add 60-second timeout on `_send_request` via `asyncio.wait_for`
    - Handle JSON-RPC error responses and return `{"error": "..."}` dicts
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 1.3 Implement subprocess spawn and initialize handshake
    - Implement `_spawn_server()` using `asyncio.create_subprocess_exec` with stdin/stdout pipes
    - Send MCP `initialize` request with protocol version and client info
    - Send `notifications/initialized` notification after handshake
    - Pass current process environment to subprocess (`env=None` inherits os.environ)
    - _Requirements: 1.1, 8.3_

  - [x] 1.4 Implement lazy startup and respawn logic
    - Implement `_ensure_server()` that checks if process is alive (`returncode is None`)
    - Spawn on first call, reuse on subsequent calls
    - Respawn transparently if process has exited unexpectedly
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 1.5 Implement shutdown method
    - Implement `shutdown()` that terminates all running subprocesses
    - Use `terminate()` first, then `kill()` after 5-second timeout
    - Clear instance registry after shutdown
    - _Requirements: 1.3_

  - [x] 1.6 Write unit tests for JSON-RPC communication
    - Test `_send_request` serialization and response parsing
    - Test timeout handling returns error dict
    - Test JSON-RPC error response propagation
    - _Requirements: 3.2, 3.3, 3.4_

  - [x] 1.7 Write property test for subprocess lifecycle
    - **Property 1: Subprocess Lifecycle — Lazy Spawn and Reuse**
    - **Validates: Requirements 1.1, 1.2**

  - [x] 1.8 Write property test for subprocess respawn after crash
    - **Property 2: Subprocess Respawn After Crash**
    - **Validates: Requirements 1.4**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Add tool discovery and schema conversion
  - [x] 3.1 Implement tool discovery in `_spawn_server()`
    - Call `tools/list` after initialize handshake
    - Store raw MCP tool schemas on the `ServerInstance`
    - Register each tool in `_tool_map` with prefixed name → (server_name, original_name)
    - Convert hyphens to underscores in registered tool names
    - _Requirements: 2.1, 2.4, 4.3_

  - [x] 3.2 Implement MCP-to-Gemini schema conversion
    - Implement `_mcp_schema_to_gemini()` converting inputSchema to Gemini parameters format
    - Apply `mcp_<prefix>_<tool_name>` naming convention
    - Preserve description and required fields
    - _Requirements: 2.2, 4.1, 4.2_

  - [x] 3.3 Implement `get_tool_declarations()` method
    - Aggregate declarations from all configured servers
    - Ensure all servers are started (call `_ensure_server` for each)
    - Return combined list of Gemini-compatible FunctionDeclaration dicts
    - _Requirements: 2.3_

  - [x] 3.4 Implement `call_tool()` dispatch routing
    - Look up prefixed name in `_tool_map` to find server and original tool name
    - Call `_ensure_server` then `_send_request` with `tools/call` method
    - Extract text content from MCP response and parse as JSON
    - Return `{"error": "Unknown tool: X"}` for unregistered tools
    - _Requirements: 2.4, 3.1_

  - [x] 3.5 Write property test for schema conversion correctness
    - **Property 3: Schema Conversion Correctness**
    - **Validates: Requirements 2.2, 4.1, 4.3**

  - [x] 3.6 Write property test for combined declarations aggregation
    - **Property 4: Combined Declarations Aggregation**
    - **Validates: Requirements 2.3**

  - [x] 3.7 Write property test for tool routing correctness
    - **Property 5: Tool Routing Correctness**
    - **Validates: Requirements 2.4, 3.1**

  - [x] 3.8 Write property test for error response propagation
    - **Property 7: Error Response Propagation**
    - **Validates: Requirements 3.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Wire MCPManager into agent.py in dual mode
  - [x] 5.1 Add MCPManager lifecycle to `main.py`
    - Add `asynccontextmanager` lifespan to FastAPI app
    - Initialize `MCPManager` with `build_server_configs()` on startup
    - Call `mcp.discover_all_tools()` during startup (or lazy on first request)
    - Call `mcp.shutdown()` on application shutdown
    - Store manager instance as module-level variable accessible to endpoints
    - _Requirements: 1.3, 1.5_

  - [x] 5.2 Update `agent.py` to accept MCPManager and use dual-mode dispatch
    - Add `mcp: MCPManager` parameter to `run_agent()`
    - Get declarations from `mcp.get_tool_declarations()` and merge with existing `TOOL_DECLARATIONS`
    - In tool execution: try `mcp.call_tool()` first, fall back to `TOOL_REGISTRY` if unknown
    - _Requirements: 2.3, 3.1_

  - [x] 5.3 Update geo-event emission for MCP tool names
    - Add `GEO_ROUTE_PATTERNS` and `GEO_POINT_PATTERNS` for pattern matching
    - Emit `map` SSE events for `mcp_*` prefixed route tools (geometry extraction)
    - Emit `map` SSE events for `mcp_*` prefixed geocode tools (coordinate extraction)
    - Strip geometry from result before sending to LLM (context savings)
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 5.4 Write property test for geo-event emission
    - **Property 9: Geo-Event Emission**
    - **Validates: Requirements 9.1, 9.2, 9.3**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Inline lib modules into MCP servers
  - [x] 7.1 Copy required lib modules into each MCP server directory
    - For each of the 8 MCP servers, identify which `lib/src/lib/*.py` modules it imports
    - Copy those modules into the MCP server directory (e.g. `mcp/brouter/lib_brouter.py` or inline)
    - Update imports in each `server.py` to use local modules instead of `from lib.*`
    - _Requirements: 7.1_

  - [x] 7.2 Remove `trip-planner-lib` workspace dependency from MCP server pyproject.toml files
    - Remove `trip-planner-lib` from `dependencies` in each MCP server's `pyproject.toml`
    - Remove `[tool.uv.sources]` section referencing the workspace source
    - _Requirements: 7.3_

  - [x] 7.3 Remove `trip-planner-lib` dependency from backend pyproject.toml
    - Remove `trip-planner-lib` from `dependencies` in `app/backend/pyproject.toml`
    - Remove `[tool.uv.sources]` section referencing the workspace source
    - _Requirements: 7.2_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Remove static tool registry and switch to MCP-only
  - [x] 9.1 Remove dual-mode fallback from `agent.py`
    - Remove `TOOL_REGISTRY` import and fallback logic
    - Use only `mcp.call_tool()` for all tool invocations
    - Remove `TOOL_DECLARATIONS` import (declarations come from MCPManager)
    - _Requirements: 5.1_

  - [x] 9.2 Delete `app/backend/tools.py`
    - Remove the entire `tools.py` file
    - Remove any remaining imports of `tools` module in the backend
    - _Requirements: 5.2, 5.3_

- [x] 10. Remove steering sanitization
  - [x] 10.1 Simplify `steering.py` — remove sanitization logic
    - Remove `_SECTIONS_TO_STRIP` list
    - Remove `_sanitize_steering()` function
    - Remove the "Tool Mapping" section from the base system prompt
    - Remove the "STRICT" tool availability warnings (tools now match steering names)
    - Load steering files directly without rewriting `mcp_` prefixed names
    - Update `build_system_prompt()` to accept tool names list from MCPManager
    - Remove `from tools import TOOL_DECLARATIONS` import
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 10.2 Write property test for steering passthrough
    - **Property 8: Steering Passthrough**
    - **Validates: Requirements 6.1**

- [x] 11. Delete lib directory and final cleanup
  - [x] 11.1 Delete the `lib/` directory at project root
    - Remove `lib/` directory and all its contents
    - _Requirements: 7.1_

  - [x] 11.2 Clean up workspace-level pyproject.toml and uv workspace config
    - Remove any workspace member references to `lib/`
    - Run `uv lock` in affected directories to regenerate lock files
    - _Requirements: 7.2, 7.3_

  - [x] 11.3 Write smoke tests for migration completeness
    - Verify no `lib.*` imports remain in backend code
    - Verify no `_sanitize_steering` function exists
    - Verify no `TOOL_REGISTRY` dict exists in backend
    - Verify all 8 MCP servers can be spawned and respond to `tools/list`
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 7.1_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The dual-mode transition (Phase 3/task 5) ensures the app remains functional during migration
- Library inlining (task 7) must happen before removing the static registry (task 9)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4", "1.5"] },
    { "id": 3, "tasks": ["1.6", "1.7", "1.8"] },
    { "id": 4, "tasks": ["3.1", "3.2"] },
    { "id": 5, "tasks": ["3.3", "3.4"] },
    { "id": 6, "tasks": ["3.5", "3.6", "3.7", "3.8"] },
    { "id": 7, "tasks": ["5.1"] },
    { "id": 8, "tasks": ["5.2", "5.3"] },
    { "id": 9, "tasks": ["5.4"] },
    { "id": 10, "tasks": ["7.1"] },
    { "id": 11, "tasks": ["7.2", "7.3"] },
    { "id": 12, "tasks": ["9.1"] },
    { "id": 13, "tasks": ["9.2"] },
    { "id": 14, "tasks": ["10.1"] },
    { "id": 15, "tasks": ["10.2"] },
    { "id": 16, "tasks": ["11.1", "11.2"] },
    { "id": 17, "tasks": ["11.3"] }
  ]
}
```
