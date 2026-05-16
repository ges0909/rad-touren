"""Property test: Error Response Propagation.

**Validates: Requirements 3.4**

For any JSON-RPC error response from an MCP server (with varying error codes
and messages), the MCPManager SHALL return a dict containing an "error" key
whose value includes the original error message text.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from mcp_manager import MCPManager, ServerConfig, ServerInstance

# Strategy: JSON-RPC error codes (standard range -32700 to -32000, plus custom)
error_codes = st.one_of(
    st.integers(min_value=-32700, max_value=-32000),  # standard JSON-RPC errors
    st.integers(min_value=-32099, max_value=-32000),  # server errors
    st.integers(min_value=1, max_value=10000),  # custom positive codes
    st.integers(min_value=-99999, max_value=-1),  # custom negative codes
)

# Strategy: non-empty error messages
error_messages = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())


def _make_manager_with_tool() -> tuple[MCPManager, MagicMock]:
    """Create an MCPManager with a registered tool and mock process."""
    config = ServerConfig(
        name="test-server",
        prefix="test",
        command=["echo", "noop"],
        cwd=Path("/tmp"),
    )
    manager = MCPManager(configs=[config])

    # Create mock process
    process = MagicMock()
    process.returncode = None
    process.pid = 99999
    process.stdin = MagicMock()
    process.stdin.write = MagicMock()
    process.stdin.drain = AsyncMock()
    process.stdout = MagicMock()
    process.stdout.readline = AsyncMock()

    # Register a tool and server instance
    instance = ServerInstance(config=config, process=process)
    manager._instances["test-server"] = instance
    manager._tool_map["mcp_test_some_tool"] = ("test-server", "some_tool")

    return manager, process


@given(error_code=error_codes, error_message=error_messages)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_error_response_propagation(error_code: int, error_message: str) -> None:
    """Property 7: JSON-RPC error responses propagate through call_tool.

    **Validates: Requirements 3.4**

    For any JSON-RPC error response with a code and message, calling call_tool
    SHALL return a dict with an "error" key whose value includes the original
    error message text.
    """
    manager, mock_process = _make_manager_with_tool()

    # Configure mock stdout to return a JSON-RPC error response
    jsonrpc_error_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": error_code,
            "message": error_message,
        },
    }
    mock_process.stdout.readline.return_value = (json.dumps(jsonrpc_error_response) + "\n").encode()

    # Call the tool
    result = await manager.call_tool("mcp_test_some_tool", {"arg": "value"})

    # Assert: result is a dict with an "error" key
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "error" in result, f"Expected 'error' key in result: {result}"

    # Assert: the error value contains the original error message
    assert error_message in result["error"], (
        f"Expected error message '{error_message}' to be contained in "
        f"result['error'] = '{result['error']}'"
    )
