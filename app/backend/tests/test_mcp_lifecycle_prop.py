"""Property test: Subprocess Lifecycle — Lazy Spawn and Reuse.

**Validates: Requirements 1.1, 1.2**

For any sequence of tool calls targeting the same MCP server, the first call
SHALL trigger exactly one subprocess spawn, and all subsequent calls SHALL
reuse that same subprocess (no additional spawns occur while the process is alive).
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from mcp_manager import MCPManager, ServerConfig, ServerInstance


def _make_test_config(name: str = "test-server") -> ServerConfig:
    """Create a minimal ServerConfig for testing."""
    return ServerConfig(
        name=name,
        prefix="test",
        command=["echo", "noop"],
        cwd=Path("/tmp"),
    )


def _make_mock_process() -> MagicMock:
    """Create a mock process that appears alive (returncode=None)."""
    process = MagicMock()
    process.returncode = None
    process.pid = 12345
    process.stdin = MagicMock()
    process.stdin.write = MagicMock()
    process.stdin.drain = AsyncMock()
    process.stdout = MagicMock()
    process.stdout.readline = AsyncMock(return_value=b'{"jsonrpc":"2.0","id":1,"result":{}}\n')
    process.terminate = MagicMock()
    process.kill = MagicMock()
    process.wait = AsyncMock()
    return process


@given(num_calls=st.integers(min_value=2, max_value=10))
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_lazy_spawn_and_reuse(num_calls: int) -> None:
    """Property 1: First _ensure_server spawns exactly once; subsequent calls reuse.

    **Validates: Requirements 1.1, 1.2**
    """
    config = _make_test_config()
    manager = MCPManager([config])

    mock_process = _make_mock_process()
    mock_instance = ServerInstance(config=config, process=mock_process)

    with patch.object(manager, "_spawn_server", new_callable=AsyncMock) as mock_spawn:
        mock_spawn.return_value = mock_instance

        instances: list[ServerInstance] = []
        for _ in range(num_calls):
            instance = await manager._ensure_server("test-server")
            instances.append(instance)

        # _spawn_server called exactly once (lazy spawn on first call)
        assert mock_spawn.call_count == 1, (
            f"Expected exactly 1 spawn call, got {mock_spawn.call_count} "
            f"for {num_calls} _ensure_server calls"
        )

        # All returned instances are the same object (reuse)
        first_instance = instances[0]
        for i, inst in enumerate(instances[1:], start=1):
            assert inst is first_instance, f"Call {i} returned a different instance than call 0"
