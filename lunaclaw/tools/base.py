from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from lunaclaw.audit.tracer import TraceContext


class ToolResult(BaseModel):
    success: bool
    output: str = ""
    error: str | None = None


class BaseTool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]
    requires_approval: bool = False

    @abstractmethod
    async def execute(self, params: dict[str, Any], trace: TraceContext) -> ToolResult: ...
