from __future__ import annotations

import uuid
from pathlib import Path

from lunaclaw.rag.embeddings import EmbeddingProvider
from lunaclaw.rag.store import Document, SearchResult, VectorStore


class RAGEngine:
    def __init__(
        self,
        embedding: EmbeddingProvider,
        store: VectorStore,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> None:
        self._embedding = embedding
        self._store = store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def _chunk_text(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            chunks.append(text[start:end])
            start = end - self._chunk_overlap
            if start >= len(text):
                break
        return chunks

    async def ingest(self, text: str, source: str = "") -> int:
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        docs = [
            Document(
                id=uuid.uuid4().hex[:12],
                content=chunk,
                source=source,
                metadata={"chunk_index": i},
            )
            for i, chunk in enumerate(chunks)
        ]

        embeddings = await self._embedding.embed([d.content for d in docs])
        await self._store.add(docs, embeddings)
        return len(docs)

    async def ingest_file(self, path: Path | str) -> int:
        path = Path(path)
        text = path.read_text()
        return await self.ingest(text, source=str(path))

    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_embedding = (await self._embedding.embed([query]))[0]
        return await self._store.search(query_embedding, top_k=top_k)
