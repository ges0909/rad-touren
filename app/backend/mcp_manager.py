"""MCP subprocess manager — lazy spawn, tool discovery, call routing."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project root (two levels up from app/backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""

    name: str
    prefix: str  # e.g. "brouter", "open_meteo"
    command: list[str]  # e.g. ["uv", "run", "python", "server.py"]
    cwd: Path  # working directory


@dataclass
class ServerInstance:
    """A running MCP server subprocess."""

    config: ServerConfig
    process: asyncio.subprocess.Process
    request_id: int = 0
    tools: list[dict[str, Any]] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def next_id(self) -> int:
        self.request_id += 1
        return self.request_id


# Server name mappings: directory name → tool prefix
SERVER_PREFIX_MAP: dict[str, str] = {
    "brouter": "brouter",
    "open-meteo": "open_meteo",
    "vbb": "vbb",
    "overpass": "overpass",
    "ors": "openrouteservice",
    "osrm": "osrm",
    "wikivoyage": "wikivoyage",
    "waymarkedtrails": "waymarkedtrails",
    "tavily": "tavily",
}


def build_server_configs() -> list[ServerConfig]:
    """Build server configurations for all 8 tour-planning MCP servers."""
    servers = [
        ("brouter", "mcp/brouter"),
        ("open-meteo", "mcp/open-meteo"),
        ("vbb", "mcp/vbb"),
        ("overpass", "mcp/overpass"),
        ("ors", "mcp/ors"),
        ("osrm", "mcp/osrm"),
        ("wikivoyage", "mcp/wikivoyage"),
        ("waymarkedtrails", "mcp/waymarkedtrails"),
        ("tavily", "mcp/tavily"),
    ]
    configs: list[ServerConfig] = []
    for name, directory in servers:
        server_dir = PROJECT_ROOT / directory
        configs.append(
            ServerConfig(
                name=name,
                prefix=SERVER_PREFIX_MAP[name],
                command=["uv", "run", "--directory", str(server_dir), "python", "server.py"],
                cwd=server_dir,
            )
        )
    return configs


class MCPManager:
    """Manages MCP server subprocesses with lazy startup and tool discovery."""

    def __init__(self, configs: list[ServerConfig]) -> None:
        self._configs: dict[str, ServerConfig] = {c.name: c for c in configs}
        self._instances: dict[str, ServerInstance] = {}
        self._tool_map: dict[
            str, tuple[str, str]
        ] = {}  # prefixed_name → (server_name, original_name)
        self._declarations: list[dict[str, Any]] = []

    async def discover_all_tools(self) -> None:
        """Pre-discover tools from all configured servers in parallel."""
        await asyncio.gather(*(self._ensure_server(name) for name in self._configs))
        # Build declarations cache
        self._declarations = []
        for instance in self._instances.values():
            for tool in instance.tools:
                decl = self._mcp_schema_to_gemini(tool, instance.config.prefix)
                self._declarations.append(decl)

    async def get_tool_declarations(self) -> list[dict[str, Any]]:
        """Return combined Gemini-compatible tool declarations from all servers."""
        if not self._declarations:
            await self.discover_all_tools()
        return self._declarations

    async def call_tool(self, prefixed_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a tool call to the correct MCP server subprocess.

        Args:
            prefixed_name: Full tool name (e.g. "mcp_brouter_calculate_route").
            arguments: Tool arguments as a dict.

        Returns:
            Tool result as a dict, or {"error": "..."} on failure.
        """
        mapping = self._tool_map.get(prefixed_name)
        if not mapping:
            return {"error": f"Unknown tool: {prefixed_name}"}

        server_name, original_name = mapping

        try:
            instance = await self._ensure_server(server_name)
        except Exception as e:
            logger.error("Failed to start server %s: %s", server_name, e)
            return {"error": f"Server {server_name} unavailable: {e}"}

        try:
            result = await self._send_request(
                instance,
                "tools/call",
                {
                    "name": original_name,
                    "arguments": arguments,
                },
            )
        except TimeoutError:
            logger.error("Tool %s timed out (60s)", prefixed_name)
            return {"error": f"Tool {prefixed_name} timed out after 60 seconds"}
        except Exception as e:
            logger.error("Tool %s failed: %s", prefixed_name, e)
            return {"error": str(e)}

        # MCP tools/call returns {"content": [{"type": "text", "text": "..."}]}
        # Extract text content and parse as JSON if possible
        content = result.get("content", [])
        if content and isinstance(content, list):
            text_parts = [c["text"] for c in content if c.get("type") == "text"]
            combined = "\n".join(text_parts)
            try:
                return json.loads(combined)
            except (json.JSONDecodeError, ValueError):
                return {"text": combined}

        return result

    async def shutdown(self) -> None:
        """Terminate all running MCP server subprocesses."""
        for name, instance in self._instances.items():
            if instance.process.returncode is None:
                instance.process.terminate()
                try:
                    await asyncio.wait_for(instance.process.wait(), timeout=5.0)
                except TimeoutError:
                    instance.process.kill()
                logger.info("Terminated MCP server: %s", name)
        self._instances.clear()

    def _mcp_schema_to_gemini(self, tool: dict[str, Any], prefix: str) -> dict[str, Any]:
        """Convert an MCP tool schema to a Gemini FunctionDeclaration dict.

        MCP schema format:
            {"name": "calculate_route", "description": "...", "inputSchema": {"type": "object", "properties": {...}, "required": [...]}}

        Gemini format:
            {"name": "mcp_brouter_calculate_route", "description": "...", "parameters": {"type": "object", "properties": {...}, "required": [...]}}
        """
        original_name = tool["name"]
        prefixed_name = f"mcp_{prefix}_{original_name}".replace("-", "_")

        declaration: dict[str, Any] = {
            "name": prefixed_name,
            "description": tool.get("description", ""),
        }

        input_schema = tool.get("inputSchema", {})
        if input_schema:
            properties = input_schema.get("properties", {})
            cleaned_props = {k: self._clean_property(v) for k, v in properties.items()}
            declaration["parameters"] = {
                "type": input_schema.get("type", "object"),
                "properties": cleaned_props,
            }
            required = input_schema.get("required")
            if required:
                declaration["parameters"]["required"] = required

        return declaration

    def _clean_property(self, prop: dict[str, Any]) -> dict[str, Any]:
        """Recursively strip JSON Schema fields unsupported by Gemini.

        Gemini supports: type, description, enum, items, properties, required.
        It does NOT support: additionalProperties, anyOf, allOf, oneOf, default, $ref, etc.
        """
        # Handle anyOf/oneOf: pick the first non-null type
        for union_key in ("anyOf", "oneOf"):
            if union_key in prop:
                variants = prop[union_key]
                non_null = [v for v in variants if v.get("type") != "null"]
                if non_null:
                    # Use the first non-null variant as the base, merge description
                    resolved = dict(non_null[0])
                    if "description" in prop:
                        resolved["description"] = prop["description"]
                    # Mark as nullable by keeping description hint
                    return self._clean_property(resolved)
                # All variants are null — treat as string
                result: dict[str, Any] = {"type": "string"}
                if "description" in prop:
                    result["description"] = prop["description"]
                return result

        # Allowed keys for Gemini
        allowed = {"type", "description", "enum", "items", "properties", "required"}
        cleaned: dict[str, Any] = {}

        for key, value in prop.items():
            if key not in allowed:
                continue
            if key == "items" and isinstance(value, dict):
                cleaned["items"] = self._clean_property(value)
            elif key == "properties" and isinstance(value, dict):
                cleaned["properties"] = {k: self._clean_property(v) for k, v in value.items()}
            else:
                cleaned[key] = value

        # Ensure type is present
        if "type" not in cleaned:
            cleaned["type"] = "string"

        return cleaned

    async def _ensure_server(self, server_name: str) -> ServerInstance:
        """Ensure server is running. Spawn if not started or if process died."""
        instance = self._instances.get(server_name)
        if instance and instance.process.returncode is None:
            return instance

        # Process died or never started — (re)spawn
        config = self._configs[server_name]
        logger.info("Spawning MCP server: %s", server_name)
        instance = await self._spawn_server(config)
        self._instances[server_name] = instance
        return instance

    async def _spawn_server(self, config: ServerConfig) -> ServerInstance:
        """Spawn subprocess, perform MCP initialize handshake, discover tools."""
        process = await asyncio.create_subprocess_exec(
            *config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=config.cwd,
            env=None,  # inherit current process environment (os.environ)
            limit=1024 * 1024,  # 1MB line buffer (routes can be large)
        )

        instance = ServerInstance(config=config, process=process)

        # MCP initialize handshake
        await self._send_request(
            instance,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "trip-planner-backend", "version": "0.1.0"},
            },
        )

        # Send initialized notification
        await self._send_notification(instance, "notifications/initialized", {})

        # Discover tools
        result = await self._send_request(instance, "tools/list", {})
        instance.tools = result.get("tools", [])

        # Register tools in the global map
        for tool in instance.tools:
            original_name = tool["name"]
            prefixed = f"mcp_{config.prefix}_{original_name}".replace("-", "_")
            self._tool_map[prefixed] = (config.name, original_name)

        logger.info("Server %s ready: %d tools", config.name, len(instance.tools))
        return instance

    async def _send_request(
        self, instance: ServerInstance, method: str, params: dict[str, Any]
    ) -> Any:
        """Send JSON-RPC 2.0 request over stdin, read response from stdout."""
        request_id = await instance.next_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        payload = json.dumps(request) + "\n"
        instance.process.stdin.write(payload.encode())
        await instance.process.stdin.drain()

        # Read response line (newline-delimited JSON)
        line = await asyncio.wait_for(
            instance.process.stdout.readline(),
            timeout=60.0,
        )

        response = json.loads(line)
        if "error" in response:
            return {"error": response["error"].get("message", "Unknown MCP error")}
        return response.get("result", {})

    async def _send_notification(
        self, instance: ServerInstance, method: str, params: dict[str, Any]
    ) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        payload = json.dumps(notification) + "\n"
        instance.process.stdin.write(payload.encode())
        await instance.process.stdin.drain()
