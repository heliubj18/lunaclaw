from __future__ import annotations

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.mcp.registry import McpRegistry
from lunaclaw.tools.base import BaseTool, ToolResult


class McpTool(BaseTool):
    requires_approval = False

    def __init__(
        self, name: str, description: str, parameters: dict, registry: McpRegistry
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self._registry = registry

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        try:
            output = await self._registry.call_tool(self.name, params)
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
