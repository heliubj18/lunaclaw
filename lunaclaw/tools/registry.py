from __future__ import annotations

import time
from typing import Any

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.audit.types import TraceEvent
from lunaclaw.tools.base import BaseTool, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def generate_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, params: dict[str, Any], trace: TraceContext) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(success=False, error=f"Tool '{name}' not found")

        trace.record(
            TraceEvent(
                event_type="tool_call",
                data={"tool": name, "params": params},
            )
        )

        start = time.monotonic()
        try:
            result = await tool.execute(params, trace)
        except Exception as e:
            result = ToolResult(success=False, error=str(e))

        duration_ms = (time.monotonic() - start) * 1000
        trace.record(
            TraceEvent(
                event_type="tool_result",
                data={"tool": name, "success": result.success, "output_length": len(result.output)},
                duration_ms=duration_ms,
            )
        )

        return result
