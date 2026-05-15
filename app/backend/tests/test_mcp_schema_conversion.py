"""Unit tests for MCP-to-Gemini schema conversion.

Tests _mcp_schema_to_gemini() converting MCP tool schemas to Gemini
FunctionDeclaration format with correct naming, description, and parameters.

Validates: Requirements 2.2, 4.1, 4.2
"""

from pathlib import Path

import pytest

from mcp_manager import MCPManager, ServerConfig


@pytest.fixture
def manager() -> MCPManager:
    """An MCPManager instance for testing schema conversion."""
    return MCPManager(configs=[])


class TestNamingConvention:
    """Test mcp_<prefix>_<tool_name> naming convention."""

    def test_basic_prefixed_name(self, manager: MCPManager) -> None:
        """Verify tool name is prefixed with mcp_<prefix>_."""
        tool = {"name": "calculate_route", "description": "Calculate a route", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "brouter")
        assert result["name"] == "mcp_brouter_calculate_route"

    def test_hyphens_replaced_with_underscores(self, manager: MCPManager) -> None:
        """Verify hyphens in tool names are converted to underscores."""
        tool = {"name": "search-routes", "description": "Search routes", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "waymarkedtrails")
        assert result["name"] == "mcp_waymarkedtrails_search_routes"

    def test_hyphens_in_prefix_replaced(self, manager: MCPManager) -> None:
        """Verify hyphens in prefix are also converted to underscores."""
        tool = {"name": "forecast", "description": "Get forecast", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "open-meteo")
        assert result["name"] == "mcp_open_meteo_forecast"

    def test_open_meteo_prefix(self, manager: MCPManager) -> None:
        """Verify open_meteo prefix produces correct name."""
        tool = {"name": "weather_forecast", "description": "Weather", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "open_meteo")
        assert result["name"] == "mcp_open_meteo_weather_forecast"

    def test_openrouteservice_prefix(self, manager: MCPManager) -> None:
        """Verify openrouteservice prefix for ors server."""
        tool = {"name": "geocode", "description": "Geocode", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "openrouteservice")
        assert result["name"] == "mcp_openrouteservice_geocode"


class TestDescriptionPreservation:
    """Test that description is preserved in the output."""

    def test_description_preserved(self, manager: MCPManager) -> None:
        """Verify description is copied from MCP tool to Gemini declaration."""
        tool = {
            "name": "calculate_route",
            "description": "Calculate a cycling route through waypoints.",
            "inputSchema": {},
        }
        result = manager._mcp_schema_to_gemini(tool, "brouter")
        assert result["description"] == "Calculate a cycling route through waypoints."

    def test_missing_description_defaults_to_empty(self, manager: MCPManager) -> None:
        """Verify missing description defaults to empty string."""
        tool = {"name": "some_tool", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "test")
        assert result["description"] == ""


class TestParametersConversion:
    """Test inputSchema → parameters conversion."""

    def test_full_schema_conversion(self, manager: MCPManager) -> None:
        """Verify inputSchema is converted to parameters with type, properties, required."""
        tool = {
            "name": "calculate_route",
            "description": "Calculate route",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "waypoints": {
                        "type": "array",
                        "description": "List of [lon, lat] pairs",
                        "items": {"type": "array", "items": {"type": "number"}},
                    },
                    "profile": {
                        "type": "string",
                        "description": "Routing profile",
                        "default": "trekking",
                    },
                },
                "required": ["waypoints"],
            },
        }
        result = manager._mcp_schema_to_gemini(tool, "brouter")

        assert "parameters" in result
        params = result["parameters"]
        assert params["type"] == "object"
        assert "waypoints" in params["properties"]
        assert "profile" in params["properties"]
        assert params["required"] == ["waypoints"]

    def test_empty_input_schema_no_parameters(self, manager: MCPManager) -> None:
        """Verify empty inputSchema results in no parameters key."""
        tool = {"name": "list_tools", "description": "List tools", "inputSchema": {}}
        result = manager._mcp_schema_to_gemini(tool, "test")
        assert "parameters" not in result

    def test_missing_input_schema_no_parameters(self, manager: MCPManager) -> None:
        """Verify missing inputSchema results in no parameters key."""
        tool = {"name": "list_tools", "description": "List tools"}
        result = manager._mcp_schema_to_gemini(tool, "test")
        assert "parameters" not in result

    def test_schema_without_required_field(self, manager: MCPManager) -> None:
        """Verify schema without required field omits required from parameters."""
        tool = {
            "name": "search",
            "description": "Search",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
        }
        result = manager._mcp_schema_to_gemini(tool, "wikivoyage")

        assert "parameters" in result
        assert "required" not in result["parameters"]

    def test_schema_with_empty_required_list(self, manager: MCPManager) -> None:
        """Verify empty required list is not included in parameters."""
        tool = {
            "name": "search",
            "description": "Search",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        }
        result = manager._mcp_schema_to_gemini(tool, "wikivoyage")

        assert "parameters" in result
        assert "required" not in result["parameters"]

    def test_properties_preserved_deeply(self, manager: MCPManager) -> None:
        """Verify nested property schemas are preserved as-is."""
        tool = {
            "name": "weather_forecast",
            "description": "Get weather",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude (-90 to 90)"},
                    "longitude": {"type": "number", "description": "Longitude (-180 to 180)"},
                    "hourly": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Hourly variables",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        }
        result = manager._mcp_schema_to_gemini(tool, "open_meteo")

        params = result["parameters"]
        assert params["properties"]["latitude"] == {"type": "number", "description": "Latitude (-90 to 90)"}
        assert params["properties"]["longitude"] == {"type": "number", "description": "Longitude (-180 to 180)"}
        assert params["required"] == ["latitude", "longitude"]
