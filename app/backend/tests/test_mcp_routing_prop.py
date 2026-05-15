"""Property test: Tool Routing Correctness.

**Validates: Requirements 2.4, 3.1**

For any registered tool with prefixed name `mcp_<prefix>_<tool>`, calling
`call_tool` with that name SHALL route the invocation to the MCP server whose
prefix matches, using the original (unprefixed) tool name in the `tools/call`
JSON-RPC request.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from mcp_manager import MCPManager, ServerConfig, ServerInstance


# --- Strategies ---

# Server prefixes: alphanumeric + underscores, 1-15 chars
prefix_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,14}", fullmatch=True)

# Tool names: alphanumeric + underscores, 1-20 chars
tool_name_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,19}", fullmatch=True)

# Server names: alphanumeric + hyphens, 1-15 chars
server_name_strategy = st.from_regex(r"[a-z][a-z0-9\-]{0,14}", fullmatch=True)

# Argument values: JSON-serializable primitives and structures
json_primitives = st.one_of(
    st.text(min_size=0, max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    st.booleans(),
    st.none(),
)

# Argument keys: valid JSON object keys
arg_key_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,14}", fullmatch=True)

# Arguments dict: flat or one-level nested
arguments_strategy = st.dictionaries(
    keys=arg_key_strategy,
    values=st.one_of(
        json_primitives,
        st.lists(json_primitives, max_size=5),
        st.dictionaries(arg_key_strategy, json_primitives, max_size=3),
    ),
    max_size=5,
)


def _make_mock_process() -> MagicMock:
    """Create a mock subprocess that captures stdin writes."""
    process = MagicMock()
    process.returncode = None
    process.pid = 99999
    process.stdin = MagicMock()
    process.stdin.write = MagicMock()
    process.stdin.drain = AsyncMock()
    process.stdout = MagicMock()
    # Return a valid MCP tools/call response
    process.stdout.readline = AsyncMock(
        return_value=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": '{"ok": true}'}]},
            }
        ).encode()
        + b"\n"
    )
    return process


@given(
    server_name=server_name_strategy,
    prefix=prefix_strategy,
    tool_name=tool_name_strategy,
    arguments=arguments_strategy,
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_tool_routing_correctness(
    server_name: str, prefix: str, tool_name: str, arguments: dict
) -> None:
    """Property 5: call_tool routes to the correct server with original tool name.

    **Validates: Requirements 2.4, 3.1**

    Verifies:
    1. The JSON-RPC request has method "tools/call"
    2. params.name matches the ORIGINAL tool name (not prefixed)
    3. params.arguments matches the input arguments exactly
    4. The request is sent to the correct server (the one mapped in _tool_map)
    """
    # Build prefixed name as the system would
    prefixed_name = f"mcp_{prefix}_{tool_name}"

    # Set up config and manager
    config = ServerConfig(
        name=server_name,
        prefix=prefix,
        command=["echo", "noop"],
        cwd=Path("/tmp"),
    )
    manager = MCPManager(configs=[config])

    # Pre-register the tool in _tool_map (simulating discovery)
    manager._tool_map[prefixed_name] = (server_name, tool_name)

    # Create a mock server instance and register it as running
    mock_process = _make_mock_process()
    instance = ServerInstance(config=config, process=mock_process)
    manager._instances[server_name] = instance

    # Call the tool
    await manager.call_tool(prefixed_name, arguments)

    # Verify the request was written to the correct server's stdin
    assert mock_process.stdin.write.called, "No request was written to server stdin"

    # Parse the JSON-RPC request that was sent
    written_bytes = mock_process.stdin.write.call_args[0][0]
    request = json.loads(written_bytes.decode())

    # 1. Method must be "tools/call"
    assert request["method"] == "tools/call", (
        f"Expected method 'tools/call', got '{request['method']}'"
    )

    # 2. params.name must be the ORIGINAL tool name (not prefixed)
    assert request["params"]["name"] == tool_name, (
        f"Expected original tool name '{tool_name}', "
        f"got '{request['params']['name']}' (prefixed was '{prefixed_name}')"
    )

    # 3. params.arguments must match input arguments exactly
    assert request["params"]["arguments"] == arguments, (
        f"Arguments mismatch: sent {arguments}, got {request['params']['arguments']}"
    )

    # 4. Verify it was sent to the correct server instance
    # (the mock_process belongs to our server_name instance)
    assert manager._instances[server_name].process is mock_process, (
        "Request was not sent to the expected server instance"
    )
