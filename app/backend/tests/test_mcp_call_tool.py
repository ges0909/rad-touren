"""Unit tests for MCPManager.call_tool() dispatch routing.

Tests tool map lookup, server dispatch, MCP response content extraction,
timeout handling, and unknown tool error responses.

Validates: Requirements 2.4, 3.1
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_manager import MCPManager, ServerConfig, ServerInstance


@pytest.fixture
def server_config() -> ServerConfig:
    """A minimal server config for testing."""
    return ServerConfig(
        name="brouter",
        prefix="brouter",
        command=["python", "server.py"],
        cwd=Path("/tmp"),
    )


@pytest.fixture
def mock_process() -> MagicMock:
    """A mock asyncio subprocess with stdin/stdout pipes."""
    process = MagicMock()
    process.returncode = None
    process.pid = 12345
    process.stdin = MagicMock()
    process.stdin.write = MagicMock()
    process.stdin.drain = AsyncMock()
    process.stdout = MagicMock()
    process.stdout.readline = AsyncMock()
    return process


@pytest.fixture
def manager_with_tool(server_config: ServerConfig, mock_process: MagicMock) -> MCPManager:
    """An MCPManager with a pre-registered tool and running server instance."""
    manager = MCPManager(configs=[server_config])
    instance = ServerInstance(config=server_config, process=mock_process)
    manager._instances["brouter"] = instance
    manager._tool_map["mcp_brouter_calculate_route"] = ("brouter", "calculate_route")
    return manager


class TestUnknownToolHandling:
    """Test that unregistered tools return an error dict."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self) -> None:
        """Verify unknown tool name returns {"error": "Unknown tool: X"}."""
        manager = MCPManager(configs=[])
        result = await manager.call_tool("mcp_fake_nonexistent", {"arg": "value"})
        assert result == {"error": "Unknown tool: mcp_fake_nonexistent"}

    @pytest.mark.asyncio
    async def test_empty_tool_map_returns_error(self) -> None:
        """Verify call_tool with empty tool map returns error."""
        manager = MCPManager(configs=[])
        result = await manager.call_tool("mcp_brouter_calculate_route", {})
        assert result == {"error": "Unknown tool: mcp_brouter_calculate_route"}


class TestToolDispatchRouting:
    """Test that call_tool routes to the correct server with original tool name."""

    @pytest.mark.asyncio
    async def test_routes_to_correct_server(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify call_tool sends tools/call with original name to correct server."""
        # Mock the response: MCP tools/call returns content array
        mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": '{"distance": 42.5}'}]},
        }
        mock_process.stdout.readline.return_value = (json.dumps(mcp_response) + "\n").encode()

        result = await manager_with_tool.call_tool(
            "mcp_brouter_calculate_route", {"waypoints": [[13.4, 52.5], [13.5, 52.6]]}
        )

        # Verify the request sent to the server uses the original tool name
        written_bytes = mock_process.stdin.write.call_args[0][0]
        request = json.loads(written_bytes.decode())
        assert request["method"] == "tools/call"
        assert request["params"]["name"] == "calculate_route"
        assert request["params"]["arguments"] == {"waypoints": [[13.4, 52.5], [13.5, 52.6]]}

    @pytest.mark.asyncio
    async def test_parses_json_text_content(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify JSON text content is parsed into a dict."""
        mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": '{"route": [[52.5, 13.4], [52.6, 13.5]]}'}]
            },
        }
        mock_process.stdout.readline.return_value = (json.dumps(mcp_response) + "\n").encode()

        result = await manager_with_tool.call_tool("mcp_brouter_calculate_route", {})
        assert result == {"route": [[52.5, 13.4], [52.6, 13.5]]}

    @pytest.mark.asyncio
    async def test_non_json_text_returns_text_dict(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify non-JSON text content returns {"text": "..."}."""
        mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": "Route calculated successfully"}]},
        }
        mock_process.stdout.readline.return_value = (json.dumps(mcp_response) + "\n").encode()

        result = await manager_with_tool.call_tool("mcp_brouter_calculate_route", {})
        assert result == {"text": "Route calculated successfully"}

    @pytest.mark.asyncio
    async def test_multiple_text_parts_combined(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify multiple text content parts are joined with newlines."""
        mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {"type": "text", "text": '{"part1": 1,'},
                    {"type": "text", "text": '"part2": 2}'},
                ]
            },
        }
        mock_process.stdout.readline.return_value = (json.dumps(mcp_response) + "\n").encode()

        result = await manager_with_tool.call_tool("mcp_brouter_calculate_route", {})
        # Combined text is '{"part1": 1,\n"part2": 2}' which is valid JSON
        assert result == {"part1": 1, "part2": 2}

    @pytest.mark.asyncio
    async def test_empty_content_returns_raw_result(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify empty content list returns the raw result dict."""
        mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": []},
        }
        mock_process.stdout.readline.return_value = (json.dumps(mcp_response) + "\n").encode()

        result = await manager_with_tool.call_tool("mcp_brouter_calculate_route", {})
        assert result == {"content": []}


class TestErrorHandling:
    """Test error scenarios in call_tool."""

    @pytest.mark.asyncio
    async def test_timeout_returns_error_dict(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify timeout returns descriptive error dict."""
        mock_process.stdout.readline.side_effect = asyncio.TimeoutError()

        result = await manager_with_tool.call_tool("mcp_brouter_calculate_route", {})
        assert result == {"error": "Tool mcp_brouter_calculate_route timed out after 60 seconds"}

    @pytest.mark.asyncio
    async def test_server_spawn_failure_returns_error(self) -> None:
        """Verify server spawn failure returns error dict."""
        config = ServerConfig(name="broken", prefix="broken", command=["false"], cwd=Path("/tmp"))
        manager = MCPManager(configs=[config])
        manager._tool_map["mcp_broken_tool"] = ("broken", "tool")

        # Patch _ensure_server to raise
        with patch.object(manager, "_ensure_server", side_effect=RuntimeError("spawn failed")):
            result = await manager.call_tool("mcp_broken_tool", {})

        assert "error" in result
        assert "unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_generic_exception_returns_error(
        self, manager_with_tool: MCPManager, mock_process: MagicMock
    ) -> None:
        """Verify generic exceptions during tool call return error dict."""
        mock_process.stdout.readline.side_effect = ConnectionError("pipe broken")

        result = await manager_with_tool.call_tool("mcp_brouter_calculate_route", {})
        assert result == {"error": "pipe broken"}
