from __future__ import annotations

from lunaclaw.memory.store import MemoryStore, Memory


class MemoryIndex:
    """Retrieves relevant memories for system prompt injection."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def get_relevant(self, query: str, max_results: int = 5) -> list[Memory]:
        return (await self._store.search(query))[:max_results]

    async def format_for_prompt(self, query: str) -> str:
        memories = await self.get_relevant(query)
        if not memories:
            return ""
        lines = ["## Relevant Memories\n"]
        for m in memories:
            lines.append(f"- [{m.category}] {m.content}")
        return "\n".join(lines)
