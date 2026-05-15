"""Unit tests for MCP Manager JSON-RPC communication layer.

Tests _send_request serialization, response parsing, timeout handling,
and JSON-RPC error response propagation.

Validates: Requirements 3.2, 3.3, 3.4
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
        name="test-server",
        prefix="test",
        command=["python", "server.py"],
        cwd=Path("/tmp"),
    )


@pytest.fixture
def mock_process() -> MagicMock:
    """A mock asyncio subprocess with stdin/stdout pipes."""
    process = MagicMock()
    process.returncode = None
    process.pid = 12345

    # stdin mock
    process.stdin = MagicMock()
    process.stdin.write = MagicMock()
    process.stdin.drain = AsyncMock()

    # stdout mock
    process.stdout = MagicMock()
    process.stdout.readline = AsyncMock()

    return process


@pytest.fixture
def server_instance(server_config: ServerConfig, mock_process: MagicMock) -> ServerInstance:
    """A ServerInstance with a mocked subprocess."""
    return ServerInstance(config=server_config, process=mock_process)


class TestSendRequestSerialization:
    """Test that _send_request writes correct JSON-RPC format to stdin."""

    @pytest.mark.asyncio
    async def test_serializes_jsonrpc_request(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify correct JSON-RPC 2.0 request is written to stdin."""
        # Arrange: mock stdout to return a valid response
        response = {"jsonrpc": "2.0", "id": 1, "result": {"status": "ok"}}
        mock_process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        manager = MCPManager(configs=[])

        # Act
        await manager._send_request(server_instance, "tools/list", {"cursor": None})

        # Assert: verify what was written to stdin
        mock_process.stdin.write.assert_called_once()
        written_bytes = mock_process.stdin.write.call_args[0][0]
        written_str = written_bytes.decode()

        # Must end with newline (newline-delimited JSON)
        assert written_str.endswith("\n")

        # Parse the written JSON
        request = json.loads(written_str)
        assert request["jsonrpc"] == "2.0"
        assert request["id"] == 1
        assert request["method"] == "tools/list"
        assert request["params"] == {"cursor": None}

    @pytest.mark.asyncio
    async def test_increments_request_id(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify request IDs increment with each call."""
        response1 = {"jsonrpc": "2.0", "id": 1, "result": {}}
        response2 = {"jsonrpc": "2.0", "id": 2, "result": {}}
        mock_process.stdout.readline.side_effect = [
            (json.dumps(response1) + "\n").encode(),
            (json.dumps(response2) + "\n").encode(),
        ]

        manager = MCPManager(configs=[])

        await manager._send_request(server_instance, "initialize", {})
        await manager._send_request(server_instance, "tools/list", {})

        # Check both calls wrote different IDs
        calls = mock_process.stdin.write.call_args_list
        first_request = json.loads(calls[0][0][0].decode())
        second_request = json.loads(calls[1][0][0].decode())

        assert first_request["id"] == 1
        assert second_request["id"] == 2

    @pytest.mark.asyncio
    async def test_drains_stdin_after_write(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify stdin.drain() is called after writing."""
        response = {"jsonrpc": "2.0", "id": 1, "result": {}}
        mock_process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        manager = MCPManager(configs=[])
        await manager._send_request(server_instance, "initialize", {})

        mock_process.stdin.drain.assert_awaited_once()


class TestSendRequestResponseParsing:
    """Test that _send_request correctly parses JSON-RPC responses."""

    @pytest.mark.asyncio
    async def test_parses_valid_result(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify a valid JSON-RPC result is extracted and returned."""
        result_data = {
            "tools": [
                {"name": "calculate_route", "description": "Calculate a route", "inputSchema": {}}
            ]
        }
        response = {"jsonrpc": "2.0", "id": 1, "result": result_data}
        mock_process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        manager = MCPManager(configs=[])
        result = await manager._send_request(server_instance, "tools/list", {})

        assert result == result_data

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_result_missing(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify empty dict is returned when response has no result key."""
        response = {"jsonrpc": "2.0", "id": 1}
        mock_process.stdout.readline.return_value = (json.dumps(response) + "\n").encode()

        manager = MCPManager(configs=[])
        result = await manager._send_request(server_instance, "tools/list", {})

        assert result == {}


class TestTimeoutHandling:
    """Test that timeout returns an error dict (Requirement 3.3)."""

    @pytest.mark.asyncio
    async def test_timeout_raises_asyncio_timeout_error(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify that when readline exceeds 60s, asyncio.TimeoutError is raised.

        The MCPManager._send_request uses asyncio.wait_for with timeout=60.0.
        When it times out, the TimeoutError propagates to the caller (call_tool
        catches it and returns an error dict).
        """
        # Make readline hang forever (simulating a timeout)
        mock_process.stdout.readline.side_effect = asyncio.TimeoutError()

        manager = MCPManager(configs=[])

        with pytest.raises(asyncio.TimeoutError):
            await manager._send_request(server_instance, "tools/call", {"name": "slow_tool"})

    @pytest.mark.asyncio
    async def test_timeout_propagates_from_wait_for(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify asyncio.wait_for timeout (60s) triggers TimeoutError.

        When the server doesn't respond within 60 seconds, the caller
        (call_tool) is expected to catch this and return an error dict
        like {"error": "Tool X timed out after 60 seconds"}.
        """
        manager = MCPManager(configs=[])

        # Patch asyncio.wait_for to simulate the 60s timeout expiring
        with patch("mcp_manager.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            with pytest.raises(asyncio.TimeoutError):
                await manager._send_request(server_instance, "tools/call", {"name": "slow"})


class TestJsonRpcErrorPropagation:
    """Test that JSON-RPC error responses are propagated correctly (Requirement 3.4)."""

    @pytest.mark.asyncio
    async def test_error_response_returns_error_dict(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify JSON-RPC error response is converted to {"error": "message"}."""
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Invalid Request"},
        }
        mock_process.stdout.readline.return_value = (json.dumps(error_response) + "\n").encode()

        manager = MCPManager(configs=[])
        result = await manager._send_request(server_instance, "tools/call", {"name": "bad_tool"})

        assert result == {"error": "Invalid Request"}

    @pytest.mark.asyncio
    async def test_error_response_with_different_codes(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify various JSON-RPC error codes propagate the message."""
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }
        mock_process.stdout.readline.return_value = (json.dumps(error_response) + "\n").encode()

        manager = MCPManager(configs=[])
        result = await manager._send_request(server_instance, "tools/call", {"name": "unknown"})

        assert result == {"error": "Method not found"}

    @pytest.mark.asyncio
    async def test_error_response_without_message_uses_fallback(
        self, server_instance: ServerInstance, mock_process: MagicMock
    ) -> None:
        """Verify fallback message when error has no message field."""
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32000},
        }
        mock_process.stdout.readline.return_value = (json.dumps(error_response) + "\n").encode()

        manager = MCPManager(configs=[])
        result = await manager._send_request(server_instance, "tools/call", {})

        assert result == {"error": "Unknown MCP error"}
