"""Property test: Combined Declarations Aggregation.

**Validates: Requirements 2.3**

For any set of N configured MCP servers each exposing M_i tools, the combined
tool declarations list SHALL contain exactly sum(M_i) entries, each with a
unique prefixed name.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from mcp_manager import MCPManager, ServerConfig, ServerInstance


# --- Strategies ---

# Generate unique server names and prefixes
_server_names = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=8)

_tool_names = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=2, max_size=12).filter(
    lambda s: not s.startswith("_") and not s.endswith("_") and "__" not in s
)


@st.composite
def server_with_tools(draw: st.DrawFn) -> tuple[ServerConfig, list[dict]]:
    """Generate a server config paired with a list of unique MCP tool schemas."""
    name = draw(_server_names)
    prefix = draw(_server_names)
    num_tools = draw(st.integers(min_value=1, max_value=8))
    tool_names = draw(st.lists(_tool_names, min_size=num_tools, max_size=num_tools, unique=True))

    config = ServerConfig(
        name=name,
        prefix=prefix,
        command=["echo", "noop"],
        cwd=Path("/tmp"),
    )

    tools = [
        {
            "name": tool_name,
            "description": f"Tool {tool_name}",
            "inputSchema": {
                "type": "object",
                "properties": {"arg": {"type": "string"}},
            },
        }
        for tool_name in tool_names
    ]

    return (config, tools)


@st.composite
def multiple_servers_with_tools(
    draw: st.DrawFn,
) -> list[tuple[ServerConfig, list[dict]]]:
    """Generate 1-5 servers with unique names/prefixes and unique tools."""
    num_servers = draw(st.integers(min_value=1, max_value=5))
    # Generate unique names and prefixes for all servers
    names = draw(st.lists(_server_names, min_size=num_servers, max_size=num_servers, unique=True))
    prefixes = draw(
        st.lists(_server_names, min_size=num_servers, max_size=num_servers, unique=True)
    )

    servers = []
    for name, prefix in zip(names, prefixes):
        num_tools = draw(st.integers(min_value=1, max_value=8))
        tool_names = draw(
            st.lists(_tool_names, min_size=num_tools, max_size=num_tools, unique=True)
        )

        config = ServerConfig(
            name=name,
            prefix=prefix,
            command=["echo", "noop"],
            cwd=Path("/tmp"),
        )

        tools = [
            {
                "name": tool_name,
                "description": f"Tool {tool_name}",
                "inputSchema": {
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                },
            }
            for tool_name in tool_names
        ]

        servers.append((config, tools))

    return servers


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


@given(servers_data=multiple_servers_with_tools())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_combined_declarations_count_and_uniqueness(
    servers_data: list[tuple[ServerConfig, list[dict]]],
) -> None:
    """Property 4: Combined declarations == sum(M_i) with all unique names.

    **Validates: Requirements 2.3**
    """
    configs = [config for config, _ in servers_data]
    manager = MCPManager(configs)

    # Populate _instances directly with mock server instances containing tools
    for config, tools in servers_data:
        mock_process = _make_mock_process()
        instance = ServerInstance(config=config, process=mock_process)
        instance.tools = tools

        # Register tools in the tool map (mimics _spawn_server behavior)
        for tool in tools:
            original_name = tool["name"]
            prefixed = f"mcp_{config.prefix}_{original_name}".replace("-", "_")
            manager._tool_map[prefixed] = (config.name, original_name)

        manager._instances[config.name] = instance

    # Mock _ensure_server to return existing instances (no actual spawning)
    async def mock_ensure_server(server_name: str) -> ServerInstance:
        return manager._instances[server_name]

    with patch.object(manager, "_ensure_server", side_effect=mock_ensure_server):
        declarations = await manager.get_tool_declarations()

    # Property assertion 1: Total declarations == sum of all tools
    expected_total = sum(len(tools) for _, tools in servers_data)
    assert len(declarations) == expected_total, (
        f"Expected {expected_total} declarations, got {len(declarations)}"
    )

    # Property assertion 2: All declaration names are unique
    names = [d["name"] for d in declarations]
    assert len(names) == len(set(names)), (
        f"Duplicate declaration names found: {[n for n in names if names.count(n) > 1]}"
    )

    # Property assertion 3: Each declaration name starts with "mcp_"
    for name in names:
        assert name.startswith("mcp_"), f"Declaration name '{name}' does not start with 'mcp_'"
