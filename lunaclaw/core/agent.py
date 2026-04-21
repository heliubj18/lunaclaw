from __future__ import annotations

import json
from typing import Any

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.audit.types import TraceEvent
from lunaclaw.core.config import Config
from lunaclaw.core.context import ContextManager
from lunaclaw.core.events import (
    AssistantMessage,
    EventStream,
    ToolResultEvent,
    UserMessage,
)
from lunaclaw.llm.provider import LLMProvider
from lunaclaw.tools.registry import ToolRegistry

SYSTEM_PROMPT = """You are Lunaclaw, a helpful CLI assistant. You have access to tools for file operations, shell commands, web search, RAG knowledge base, MCP integrations, and memory.

Use tools when they help answer the user's request. Be concise and direct.
"""


class AgentLoop:
    def __init__(
        self,
        config: Config,
        provider: LLMProvider,
        registry: ToolRegistry,
        max_iterations: int = 20,
        system_prompt: str | None = None,
        memory_context: str = "",
    ) -> None:
        self._config = config
        self._provider = provider
        self._registry = registry
        self._max_iterations = max_iterations
        self._system_prompt = system_prompt or SYSTEM_PROMPT
        self._memory_context = memory_context
        self._stream = EventStream()
        self._context = ContextManager()
        self._approval_callback: Any = None

    def set_approval_callback(self, callback: Any) -> None:
        """Set a callback for tool approval: async fn(tool_name, params) -> bool"""
        self._approval_callback = callback

    async def process(self, user_input: str) -> str:
        trace = TraceContext()
        trace.record(TraceEvent(event_type="user_input", data={"query": user_input}))

        self._stream.add(UserMessage(content=user_input))

        for iteration in range(self._max_iterations):
            system = self._system_prompt
            if self._memory_context:
                system += "\n\n" + self._memory_context

            messages = [{"role": "system", "content": system}]
            messages.extend(self._context.fit_to_window(self._stream.to_messages()))

            response = await self._provider.complete(
                messages=messages,
                tools=self._registry.generate_schemas(),
                trace=trace,
            )

            if not response.tool_calls:
                content = response.content or ""
                self._stream.add(AssistantMessage(content=content))
                trace.record(TraceEvent(event_type="final_output", data={"content": content}))
                return content

            self._stream.add(
                AssistantMessage(
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            for tc in response.tool_calls:
                tool_name = tc["name"]
                try:
                    arguments = (
                        json.loads(tc["arguments"])
                        if isinstance(tc["arguments"], str)
                        else tc["arguments"]
                    )
                except json.JSONDecodeError:
                    arguments = {}

                tool = self._registry.get(tool_name)
                if tool and tool.requires_approval and self._approval_callback:
                    approved = await self._approval_callback(tool_name, arguments)
                    if not approved:
                        self._stream.add(
                            ToolResultEvent(
                                tool_call_id=tc["id"],
                                content="Tool execution denied by user",
                            )
                        )
                        continue

                result = await self._registry.execute(tool_name, arguments, trace)
                self._stream.add(
                    ToolResultEvent(
                        tool_call_id=tc["id"],
                        content=result.output if result.success else f"Error: {result.error}",
                    )
                )

        msg = "Reached max iterations. Here's what I have so far."
        trace.record(TraceEvent(event_type="error", data={"reason": "max_iterations"}))
        return msg

    def clear_history(self) -> None:
        self._stream.clear()
