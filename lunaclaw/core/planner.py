from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.audit.types import TraceEvent
from lunaclaw.core.subagent import Subagent, SubagentResult
from lunaclaw.llm.provider import LLMProvider


class PlanStep(BaseModel):
    description: str
    tool_hint: str | None = None


class PlannerResult(SubagentResult):
    steps: list[PlanStep] = []


PLANNER_SYSTEM_PROMPT = """You are a task planner. Given a user request, break it down into a sequence of concrete steps.

Return a JSON array of steps. Each step has:
- "description": what to do
- "tool_hint": (optional) which tool to use (shell, file_read, file_write, file_edit, glob, grep, rag_search, web_search, web_fetch, memory_search, etc.)

Example:
[
  {"description": "Find all Python files in the project", "tool_hint": "glob"},
  {"description": "Read the main entry point", "tool_hint": "file_read"},
  {"description": "Add the new function", "tool_hint": "file_edit"}
]

Return ONLY the JSON array, no other text."""


class PlannerSubagent(Subagent):
    name = "planner"
    system_prompt = PLANNER_SYSTEM_PROMPT

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def run(
        self,
        messages: list[dict[str, Any]],
        query: str,
        trace: TraceContext,
    ) -> PlannerResult:
        trace.record(
            TraceEvent(
                event_type="subagent_spawn",
                data={"subagent": self.name, "query": query},
            )
        )

        planner_messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]

        response = await self._provider.complete(
            messages=planner_messages,
            tools=[],
            trace=trace,
        )

        steps = self._parse_steps(response.content or "")

        return PlannerResult(
            output=f"Planned {len(steps)} steps",
            data={"steps": [s.model_dump() for s in steps]},
            steps=steps,
        )

    def _parse_steps(self, content: str) -> list[PlanStep]:
        json_match = re.search(r"\[.*\]", content, re.DOTALL)
        if json_match:
            try:
                raw = json.loads(json_match.group())
                return [PlanStep(**step) for step in raw]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        return [PlanStep(description=content or "Execute the user's request")]
