from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content: str
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryStore(ABC):
    @abstractmethod
    async def write(self, memory: Memory) -> str: ...

    @abstractmethod
    async def read(self, memory_id: str) -> Memory | None: ...

    @abstractmethod
    async def search(self, query: str) -> list[Memory]: ...

    @abstractmethod
    async def list(self, category: str | None = None) -> list[Memory]: ...

    @abstractmethod
    async def delete(self, memory_id: str) -> None: ...


class FileMemoryStore(MemoryStore):
    def __init__(self, data_dir: Path | str) -> None:
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, memory_id: str) -> Path:
        return self._dir / f"{memory_id}.json"

    async def write(self, memory: Memory) -> str:
        path = self._path(memory.id)
        path.write_text(memory.model_dump_json(indent=2))
        return memory.id

    async def read(self, memory_id: str) -> Memory | None:
        path = self._path(memory_id)
        if not path.exists():
            return None
        return Memory.model_validate_json(path.read_text())

    async def search(self, query: str) -> list[Memory]:
        query_lower = query.lower()
        results = []
        for path in self._dir.glob("*.json"):
            try:
                memory = Memory.model_validate_json(path.read_text())
                if query_lower in memory.content.lower() or any(
                    query_lower in tag.lower() for tag in memory.tags
                ):
                    results.append(memory)
            except Exception:
                continue
        return results

    async def list(self, category: str | None = None) -> list[Memory]:
        results = []
        for path in self._dir.glob("*.json"):
            try:
                memory = Memory.model_validate_json(path.read_text())
                if category is None or memory.category == category:
                    results.append(memory)
            except Exception:
                continue
        return sorted(results, key=lambda m: m.created_at, reverse=True)

    async def delete(self, memory_id: str) -> None:
        path = self._path(memory_id)
        if path.exists():
            path.unlink()
