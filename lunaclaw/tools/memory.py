from __future__ import annotations

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.memory.store import Memory, MemoryStore
from lunaclaw.tools.base import BaseTool, ToolResult


class MemoryReadTool(BaseTool):
    name = "memory_read"
    description = "Read a specific memory by ID"
    parameters = {
        "type": "object",
        "properties": {
            "memory_id": {"type": "string", "description": "The memory ID to read"},
        },
        "required": ["memory_id"],
    }
    requires_approval = False

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        memory = await self._store.read(params["memory_id"])
        if memory is None:
            return ToolResult(success=False, error="Memory not found")
        return ToolResult(success=True, output=memory.model_dump_json(indent=2))


class MemoryWriteTool(BaseTool):
    name = "memory_write"
    description = "Store a new memory"
    parameters = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The memory content"},
            "category": {
                "type": "string",
                "description": "Category: general, user, project, learned",
                "default": "general",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for the memory",
                "default": [],
            },
        },
        "required": ["content"],
    }
    requires_approval = False

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        memory = Memory(
            content=params["content"],
            category=params.get("category", "general"),
            tags=params.get("tags", []),
        )
        memory_id = await self._store.write(memory)
        return ToolResult(success=True, output=f"Memory stored with ID: {memory_id}")


class MemorySearchTool(BaseTool):
    name = "memory_search"
    description = "Search memories by query"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    }
    requires_approval = False

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        results = await self._store.search(params["query"])
        if not results:
            return ToolResult(success=True, output="No memories found")
        lines = []
        for m in results[:10]:
            lines.append(f"[{m.id}] [{m.category}] {m.content}")
        return ToolResult(success=True, output="\n".join(lines))
