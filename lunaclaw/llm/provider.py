from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from litellm import acompletion

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.audit.types import TraceEvent
from lunaclaw.core.config import Config


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[dict[str, Any]]
    usage: dict[str, int]


class LLMProvider:
    def __init__(self, config: Config) -> None:
        self.model = config.model
        self._env_overrides = config.env

    def _build_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return messages

    def _build_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        trace: TraceContext,
        model_override: str | None = None,
    ) -> LLMResponse:
        model = model_override or self.model

        trace.record(
            TraceEvent(
                event_type="llm_request",
                data={"model": model, "message_count": len(messages), "tool_count": len(tools)},
            )
        )

        # Apply env overrides for third-party providers
        old_env: dict[str, str | None] = {}
        for key, value in self._env_overrides.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": self._build_messages(messages),
            }
            if tools:
                kwargs["tools"] = self._build_tools(tools)

            response = await acompletion(**kwargs)
        finally:
            # Restore env
            for key, orig in old_env.items():
                if orig is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = orig

        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                )

        result = LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )

        trace.record(
            TraceEvent(
                event_type="llm_response",
                data={
                    "content_length": len(result.content) if result.content else 0,
                    "tool_call_count": len(result.tool_calls),
                    "usage": result.usage,
                },
            )
        )

        return result
