from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Event(BaseModel):
    role: str

    def to_message(self) -> dict[str, Any]:
        raise NotImplementedError


class UserMessage(Event):
    role: str = "user"
    content: str

    def to_message(self) -> dict[str, Any]:
        return {"role": "user", "content": self.content}


class AssistantMessage(Event):
    role: str = "assistant"
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None

    def to_message(self) -> dict[str, Any]:
        msg: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    },
                }
                for tc in self.tool_calls
            ]
        return msg


class ToolCallEvent(Event):
    role: str = "assistant"
    tool_name: str
    tool_call_id: str
    arguments: str

    def to_message(self) -> dict[str, Any]:
        return {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": self.tool_call_id,
                    "type": "function",
                    "function": {"name": self.tool_name, "arguments": self.arguments},
                }
            ],
        }


class ToolResultEvent(Event):
    role: str = "tool"
    tool_call_id: str
    content: str

    def to_message(self) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": self.content,
        }


class EventStream:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def add(self, event: Event) -> None:
        self.events.append(event)

    def to_messages(self) -> list[dict[str, Any]]:
        return [e.to_message() for e in self.events]

    def clear(self) -> None:
        self.events.clear()
