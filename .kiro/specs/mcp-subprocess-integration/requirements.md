# Requirements Document

## Introduction

Replace the static tool registry in `app/backend/tools.py` with a dynamic MCP subprocess manager. The 8 tour-planning MCP servers (brouter, open-meteo, vbb, overpass, ors, osrm, wikivoyage, waymarkedtrails) will be spawned as subprocesses using stdio transport and managed lazily (on first tool call). Tool declarations will be discovered dynamically via the MCP `tools/list` method. The shared `lib/` package will be inlined into each MCP server and removed as a workspace dependency. The steering sanitization logic that rewrites `mcp_` prefixed tool names will be removed since the agent will use `mcp_` prefixed names natively.

## Glossary

- **MCP_Manager**: The backend module responsible for spawning, tracking, and communicating with MCP server subprocesses via stdio JSON-RPC transport.
- **MCP_Server**: A FastMCP-based Python process that exposes tools via the Model Context Protocol, launched as a subprocess by the MCP_Manager.
- **Tool_Registry**: The runtime mapping of tool names to their callable implementations, dynamically built from MCP server `tools/list` responses.
- **Stdio_Transport**: The JSON-RPC communication channel using stdin/stdout pipes between the backend and MCP server subprocesses.
- **Lazy_Startup**: The pattern of deferring MCP server subprocess creation until the first tool call targeting that server is received.
- **Tool_Declaration**: A Gemini-compatible function declaration schema describing a tool's name, description, and parameters.
- **Agent_Loop**: The iterative Gemini agent cycle in `agent.py` that calls tools and feeds results back to the LLM.
- **Server_Config**: The configuration mapping that associates tool name prefixes with MCP server launch commands.

## Requirements

### Requirement 1: MCP Subprocess Lifecycle Management

**User Story:** As a backend developer, I want MCP servers to be managed as subprocesses with lazy startup, so that system resources are only consumed when tools are actually needed.

#### Acceptance Criteria

1. WHEN the Agent_Loop requests a tool belonging to an MCP_Server that has no running subprocess, THE MCP_Manager SHALL spawn the MCP_Server subprocess using stdio transport before executing the tool call.
2. WHILE an MCP_Server subprocess is running, THE MCP_Manager SHALL reuse the existing subprocess for subsequent tool calls targeting that server.
3. WHEN the backend application shuts down, THE MCP_Manager SHALL terminate all running MCP_Server subprocesses and release associated resources.
4. IF an MCP_Server subprocess exits unexpectedly, THEN THE MCP_Manager SHALL respawn the subprocess on the next tool call targeting that server.
5. THE MCP_Manager SHALL support all 8 tour-planning MCP servers: brouter, open-meteo, vbb, overpass, ors, osrm, wikivoyage, and waymarkedtrails.

### Requirement 2: Dynamic Tool Discovery

**User Story:** As a backend developer, I want tool declarations to be discovered dynamically from MCP servers, so that adding or modifying tools in an MCP server requires no changes to the backend.

#### Acceptance Criteria

1. WHEN an MCP_Server subprocess is started, THE MCP_Manager SHALL call the MCP `tools/list` method to retrieve available Tool_Declarations from that server.
2. THE MCP*Manager SHALL convert each MCP tool schema into a Gemini-compatible Tool_Declaration with the `mcp*`prefix naming convention (e.g.,`mcp_brouter_calculate_route`).
3. WHEN the Agent_Loop starts a new session, THE Tool_Registry SHALL provide Gemini with the combined Tool_Declarations from all configured MCP servers.
4. THE Tool*Registry SHALL map each `mcp*` prefixed tool name to the corresponding MCP_Server and original tool name for invocation routing.

### Requirement 3: Tool Invocation via Stdio Transport

**User Story:** As a backend developer, I want tool calls to be routed to MCP servers via JSON-RPC over stdio, so that the agent can invoke MCP tools without importing server code directly.

#### Acceptance Criteria

1. WHEN the Agent*Loop invokes a tool with an `mcp*`prefix, THE MCP_Manager SHALL route the call to the correct MCP_Server subprocess via Stdio_Transport using JSON-RPC`tools/call` method.
2. THE MCP_Manager SHALL serialize tool arguments as JSON and deserialize the MCP_Server response into a Python dict for the Agent_Loop.
3. IF an MCP_Server tool call exceeds 60 seconds, THEN THE MCP_Manager SHALL return a timeout error dict to the Agent_Loop.
4. IF an MCP_Server returns a JSON-RPC error response, THEN THE MCP_Manager SHALL return an error dict containing the error message to the Agent_Loop.

### Requirement 4: Tool Naming Convention

**User Story:** As a backend developer, I want tool names to follow the `mcp_<server>_<tool>` convention, so that steering files can reference tools without name translation.

#### Acceptance Criteria

1. THE Tool*Registry SHALL expose tools using the pattern `mcp*<server*name>*<tool_name>`where`server_name`matches the MCP server directory name (e.g.,`brouter`, `open-meteo`as`open_meteo`, `ors`as`openrouteservice`).
2. THE Tool_Registry SHALL use these server name mappings: brouter → `brouter`, open-meteo → `open_meteo`, vbb → `vbb`, overpass → `overpass`, ors → `openrouteservice`, osrm → `osrm`, wikivoyage → `wikivoyage`, waymarkedtrails → `waymarkedtrails`.
3. WHEN a tool name contains hyphens in the MCP server response, THE MCP_Manager SHALL convert hyphens to underscores in the registered tool name.

### Requirement 5: Removal of Static Tool Registry

**User Story:** As a backend developer, I want the static `tools.py` file replaced by dynamic MCP-based tool discovery, so that tool management is centralized in the MCP servers.

#### Acceptance Criteria

1. WHEN the migration is complete, THE backend SHALL obtain all tool declarations and implementations exclusively from MCP_Server subprocesses via the MCP_Manager.
2. THE backend SHALL remove the `TOOL_DECLARATIONS` list and `TOOL_REGISTRY` dict from `tools.py`.
3. THE backend SHALL remove the direct imports from `lib.*` modules in the backend package.

### Requirement 6: Removal of Steering Sanitization

**User Story:** As a backend developer, I want the steering file sanitization logic removed, so that `mcp_` prefixed tool names in steering files pass through unchanged to the LLM.

#### Acceptance Criteria

1. WHEN the migration is complete, THE steering module SHALL load steering file content without rewriting `mcp_` prefixed tool references.
2. THE steering module SHALL remove the `_sanitize_steering` function and the `_SECTIONS_TO_STRIP` configuration.
3. THE steering module SHALL remove the tool-name mapping section from the base system prompt since tool names will match steering file references directly.

### Requirement 7: Library Inlining

**User Story:** As a backend developer, I want the shared `lib/` package inlined into each MCP server, so that MCP servers are self-contained and the workspace dependency on `trip-planner-lib` is eliminated.

#### Acceptance Criteria

1. WHEN the migration is complete, each MCP_Server SHALL contain its own copy of the required library modules from `lib/src/lib/`.
2. THE backend `pyproject.toml` SHALL remove the `trip-planner-lib` dependency.
3. EACH MCP_Server `pyproject.toml` SHALL remove the `trip-planner-lib` workspace source reference.
4. THE `lib/` directory at project root SHALL be removed after inlining is complete.

### Requirement 8: Server Configuration

**User Story:** As a backend developer, I want MCP server launch commands defined in a central configuration, so that adding or reconfiguring servers requires minimal code changes.

#### Acceptance Criteria

1. THE MCP_Manager SHALL read Server_Config that maps each server identifier to its launch command (e.g., `uv run --directory mcp/brouter python server.py`).
2. THE Server_Config SHALL specify the working directory for each MCP_Server subprocess relative to the project root.
3. WHEN a Server_Config entry references an environment variable (e.g., `ORS_API_KEY`), THE MCP_Manager SHALL pass the current process environment to the subprocess.

### Requirement 9: Geo Data Event Emission

**User Story:** As a backend developer, I want the agent loop to continue emitting map events for geo tools, so that the frontend map display remains functional after the migration.

#### Acceptance Criteria

1. WHEN an MCP tool call returns route geometry data, THE Agent_Loop SHALL emit a `map` SSE event with the route coordinates in `[[lat, lng], ...]` format.
2. WHEN an MCP tool call returns geocoding results with coordinates, THE Agent_Loop SHALL emit a `map` SSE event with waypoint coordinates.
3. THE Agent_Loop SHALL identify geo-relevant tool responses by tool name pattern matching (e.g., tools containing `route`, `geocode`, `search_location`).
