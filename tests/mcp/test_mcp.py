import pytest

from lunaclaw.mcp.client import McpTransport
from lunaclaw.mcp.registry import McpRegistry


class FakeTransport(McpTransport):
    def __init__(self):
        self.connected = False
        self._tools = [
            {
                "name": "search",
                "description": "Search something",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ]

    async def connect(self) -> None:
        self.connected = True

    async def call(self, method: str, params: dict) -> dict:
        if method == "tools/list":
            return {"tools": self._tools}
        if method == "tools/call":
            return {"content": [{"type": "text", "text": f"result for {params}"}]}
        return {}

    async def close(self) -> None:
        self.connected = False


@pytest.mark.asyncio
async def test_registry_discover_tools():
    transport = FakeTransport()
    registry = McpRegistry()
    await registry.add_server("test_server", transport)

    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "mcp__test_server__search"


@pytest.mark.asyncio
async def test_registry_call_tool():
    transport = FakeTransport()
    registry = McpRegistry()
    await registry.add_server("test_server", transport)

    result = await registry.call_tool("mcp__test_server__search", {"query": "hello"})
    assert "result for" in result


@pytest.mark.asyncio
async def test_registry_call_unknown_tool():
    registry = McpRegistry()
    with pytest.raises(ValueError, match="Unknown MCP tool"):
        await registry.call_tool("mcp__unknown__tool", {})


@pytest.mark.asyncio
async def test_registry_close():
    transport = FakeTransport()
    registry = McpRegistry()
    await registry.add_server("test_server", transport)
    assert transport.connected
    await registry.close_all()
    assert not transport.connected
