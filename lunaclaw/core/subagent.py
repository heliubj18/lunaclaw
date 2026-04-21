from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from lunaclaw.audit.tracer import TraceContext


class SubagentResult(BaseModel):
    output: str
    data: dict[str, Any] = Field(default_factory=dict)


class Subagent(ABC):
    name: str
    system_prompt: str

    @abstractmethod
    async def run(
        self,
        messages: list[dict[str, Any]],
        query: str,
        trace: TraceContext,
    ) -> SubagentResult: ...
