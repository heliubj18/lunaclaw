from __future__ import annotations

from typing import Any


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


class ContextManager:
    def __init__(self, max_tokens: int = 100_000) -> None:
        self.max_tokens = max_tokens

    def fit_to_window(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not messages:
            return messages

        total = sum(_estimate_tokens(str(m)) for m in messages)
        if total <= self.max_tokens:
            return messages

        system = []
        rest = messages
        if messages[0].get("role") == "system":
            system = [messages[0]]
            rest = messages[1:]

        while rest and sum(_estimate_tokens(str(m)) for m in system + rest) > self.max_tokens:
            rest = rest[1:]

        return system + rest
