"""Property test: Subprocess Respawn After Crash.

**Validates: Requirements 1.4**

Property 2: For any MCP server whose subprocess has exited unexpectedly
(returncode is not None), the next tool call targeting that server SHALL
spawn a new subprocess and complete successfully.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from mcp_manager import MCPManager, ServerConfig, ServerInstance


def _make_config(name: str = "test-server") -> ServerConfig:
    """Create a minimal ServerConfig for testing."""
    return ServerConfig(
        name=name,
        prefix="test",
        command=["echo", "hello"],
        cwd=Path("/tmp"),
    )


def _make_crashed_instance(config: ServerConfig, exit_code: int) -> ServerInstance:
    """Create a ServerInstance with a crashed process (returncode != None)."""
    process = MagicMock()
    process.returncode = exit_code  # Non-None means crashed
    return ServerInstance(config=config, process=process)


def _make_alive_instance(config: ServerConfig) -> ServerInstance:
    """Create a ServerInstance with a live process (returncode == None)."""
    process = MagicMock()
    process.returncode = None
    return ServerInstance(config=config, process=process)


@pytest.mark.asyncio
@given(exit_code=st.integers(min_value=1, max_value=255))
@settings(max_examples=50, deadline=None)
async def test_respawn_after_crash(exit_code: int) -> None:
    """Property 2: Subprocess Respawn After Crash.

    **Validates: Requirements 1.4**

    For any exit code (1-255), when a server's process has crashed
    (returncode != None), calling _ensure_server SHALL:
    1. Spawn a NEW subprocess (call _spawn_server)
    2. The new instance has returncode == None (alive)
    3. The old crashed instance is replaced in _instances
    """
    config = _make_config()
    manager = MCPManager(configs=[config])

    # Set up a crashed instance in the manager
    crashed_instance = _make_crashed_instance(config, exit_code)
    manager._instances["test-server"] = crashed_instance

    # Create a fresh alive instance that _spawn_server will return
    new_instance = _make_alive_instance(config)

    with patch.object(manager, "_spawn_server", new_callable=AsyncMock) as mock_spawn:
        mock_spawn.return_value = new_instance

        # Call _ensure_server — should detect crash and respawn
        result = await manager._ensure_server("test-server")

        # 1. _spawn_server was called (new subprocess spawned)
        mock_spawn.assert_called_once_with(config)

        # 2. The returned instance has returncode == None (alive)
        assert result.process.returncode is None

        # 3. The old crashed instance is replaced in _instances
        assert manager._instances["test-server"] is new_instance
        assert manager._instances["test-server"] is not crashed_instance
