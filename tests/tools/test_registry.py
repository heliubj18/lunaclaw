import pytest
from lunaclaw.tools.base import BaseTool, ToolResult
from lunaclaw.tools.registry import ToolRegistry
from lunaclaw.audit.tracer import TraceContext


class MockTool(BaseTool):
    name = "mock_tool"
    description = "A mock tool for testing"
    parameters = {
        "type": "object",
        "properties": {"input": {"type": "string", "description": "Input text"}},
        "required": ["input"],
    }
    requires_approval = False

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        return ToolResult(success=True, output=f"echo: {params['input']}")


def test_register_and_get_tool():
    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)
    assert registry.get("mock_tool") is tool


def test_register_duplicate_raises():
    registry = ToolRegistry()
    registry.register(MockTool())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(MockTool())


def test_get_unknown_tool_returns_none():
    registry = ToolRegistry()
    assert registry.get("nonexistent") is None


def test_list_tools():
    registry = ToolRegistry()
    registry.register(MockTool())
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "mock_tool"


def test_generate_schemas():
    registry = ToolRegistry()
    registry.register(MockTool())
    schemas = registry.generate_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "mock_tool"
    assert schemas[0]["description"] == "A mock tool for testing"
    assert "properties" in schemas[0]["parameters"]


@pytest.mark.asyncio
async def test_execute_tool():
    registry = ToolRegistry()
    registry.register(MockTool())
    trace = TraceContext()
    result = await registry.execute("mock_tool", {"input": "hello"}, trace)
    assert result.success is True
    assert result.output == "echo: hello"
    # Should have tool_call and tool_result events
    assert len(trace.events) == 2


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    registry = ToolRegistry()
    trace = TraceContext()
    result = await registry.execute("nonexistent", {}, trace)
    assert result.success is False
    assert "not found" in result.error
