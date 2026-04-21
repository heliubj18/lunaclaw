from __future__ import annotations

from typing import Any

from lunaclaw.mcp.client import McpTransport


class McpRegistry:
    def __init__(self) -> None:
        self._servers: dict[str, McpTransport] = {}
        self._tools: dict[str, dict[str, Any]] = {}
        self._tool_to_server: dict[str, str] = {}

    async def add_server(self, name: str, transport: McpTransport) -> None:
        await transport.connect()
        self._servers[name] = transport

        result = await transport.call("tools/list", {})
        for tool in result.get("tools", []):
            full_name = f"mcp__{name}__{tool['name']}"
            self._tools[full_name] = {
                "name": full_name,
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
            }
            self._tool_to_server[full_name] = name

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools.values())

    async def call_tool(self, full_name: str, arguments: dict) -> str:
        if full_name not in self._tool_to_server:
            raise ValueError(f"Unknown MCP tool: {full_name}")

        server_name = self._tool_to_server[full_name]
        original_name = full_name.split("__", 2)[2]

        transport = self._servers[server_name]
        result = await transport.call("tools/call", {"name": original_name, "arguments": arguments})

        content = result.get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts) if texts else str(result)

    async def close_all(self) -> None:
        for transport in self._servers.values():
            await transport.close()
        self._servers.clear()
        self._tools.clear()
        self._tool_to_server.clear()
