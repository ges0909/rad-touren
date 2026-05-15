"""Smoke tests for migration completeness.

Verify the MCP subprocess integration migration is complete by checking
that legacy artifacts are removed and new infrastructure is in place.

Validates: Requirements 5.1, 5.2, 5.3, 6.1, 7.1
"""

from pathlib import Path

import pytest

# Backend directory (app/backend/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
# Project root
PROJECT_ROOT = BACKEND_DIR.parent.parent


class TestNoLibImports:
    """Verify no `lib.*` imports remain in backend code (Requirement 7.1)."""

    def test_no_from_lib_imports(self) -> None:
        """Scan all .py files in app/backend/ for 'from lib.' imports."""
        violations: list[str] = []
        for py_file in BACKEND_DIR.rglob("*.py"):
            # Skip __pycache__ and .hypothesis directories
            if "__pycache__" in str(py_file) or ".hypothesis" in str(py_file):
                continue
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("from lib.") or stripped.startswith("import lib."):
                    violations.append(f"{py_file.relative_to(BACKEND_DIR)}:{i}: {stripped}")

        assert violations == [], f"Found lib.* imports in backend:\n" + "\n".join(violations)


class TestNoSanitizeSteering:
    """Verify no `_sanitize_steering` function exists (Requirement 6.1)."""

    def test_steering_module_has_no_sanitize_function(self) -> None:
        """Import steering module and verify _sanitize_steering is not an attribute."""
        import steering

        assert not hasattr(steering, "_sanitize_steering"), (
            "steering module still has _sanitize_steering function — "
            "sanitization logic should be removed"
        )

    def test_steering_module_has_no_sections_to_strip(self) -> None:
        """Verify _SECTIONS_TO_STRIP config is also removed."""
        import steering

        assert not hasattr(steering, "_SECTIONS_TO_STRIP"), (
            "steering module still has _SECTIONS_TO_STRIP — "
            "sanitization config should be removed"
        )


class TestNoToolRegistry:
    """Verify no TOOL_REGISTRY dict exists in backend (Requirements 5.2, 5.3)."""

    def test_tools_py_does_not_exist(self) -> None:
        """Verify the file app/backend/tools.py does not exist."""
        tools_path = BACKEND_DIR / "tools.py"
        assert not tools_path.exists(), (
            f"tools.py still exists at {tools_path} — "
            "static tool registry should be removed"
        )

    def test_no_module_exports_tool_registry(self) -> None:
        """Verify no backend module exports TOOL_REGISTRY."""
        backend_modules = ["agent", "main", "mcp_manager", "steering", "i18n"]
        violations: list[str] = []

        for module_name in backend_modules:
            try:
                mod = __import__(module_name)
                if hasattr(mod, "TOOL_REGISTRY"):
                    violations.append(module_name)
            except ImportError:
                pass  # Module doesn't exist, that's fine

        assert violations == [], (
            f"TOOL_REGISTRY found in modules: {violations} — "
            "static tool registry should be removed"
        )


class TestMCPServerConfigs:
    """Verify all 8 MCP server configs are generated (Requirement 5.1)."""

    EXPECTED_SERVERS = [
        "brouter",
        "open-meteo",
        "vbb",
        "overpass",
        "ors",
        "osrm",
        "wikivoyage",
        "waymarkedtrails",
    ]

    def test_build_server_configs_returns_8_configs(self) -> None:
        """Import build_server_configs and verify it returns 8 configs."""
        from mcp_manager import build_server_configs

        configs = build_server_configs()
        assert len(configs) == 8, f"Expected 8 server configs, got {len(configs)}"

    def test_build_server_configs_has_correct_names(self) -> None:
        """Verify all 8 expected server names are present."""
        from mcp_manager import build_server_configs

        configs = build_server_configs()
        names = sorted(c.name for c in configs)
        expected = sorted(self.EXPECTED_SERVERS)
        assert names == expected, f"Server names mismatch: {names} != {expected}"

    def test_each_config_has_valid_fields(self) -> None:
        """Verify each ServerConfig has non-empty name, prefix, command, and cwd."""
        from mcp_manager import build_server_configs

        configs = build_server_configs()
        for config in configs:
            assert config.name, "ServerConfig.name is empty"
            assert config.prefix, "ServerConfig.prefix is empty"
            assert len(config.command) > 0, f"ServerConfig.command is empty for {config.name}"
            assert config.cwd, f"ServerConfig.cwd is empty for {config.name}"


class TestMCPManagerInitializes:
    """Verify MCPManager initializes correctly with all configs."""

    def test_mcp_manager_accepts_all_configs(self) -> None:
        """Create an MCPManager with build_server_configs() and verify it has 8 configs."""
        from mcp_manager import MCPManager, build_server_configs

        configs = build_server_configs()
        manager = MCPManager(configs)

        assert len(manager._configs) == 8, (
            f"MCPManager has {len(manager._configs)} configs, expected 8"
        )

    def test_mcp_manager_has_empty_instances_on_init(self) -> None:
        """Verify no servers are spawned on initialization (lazy startup)."""
        from mcp_manager import MCPManager, build_server_configs

        configs = build_server_configs()
        manager = MCPManager(configs)

        assert len(manager._instances) == 0, (
            "MCPManager should have no running instances on init (lazy startup)"
        )
