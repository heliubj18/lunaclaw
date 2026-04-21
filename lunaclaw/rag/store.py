from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    content: str
    source: str = ""
    metadata: dict = Field(default_factory=dict)


class SearchResult(BaseModel):
    document: Document
    score: float


class VectorStore(ABC):
    @abstractmethod
    async def add(self, docs: list[Document], embeddings: list[list[float]]) -> None: ...

    @abstractmethod
    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]: ...

    @abstractmethod
    async def delete(self, doc_ids: list[str]) -> None: ...


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_dir: str = "~/.lunaclaw/rag/chroma") -> None:
        import chromadb
        from pathlib import Path

        path = Path(persist_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection("lunaclaw")

    async def add(self, docs: list[Document], embeddings: list[list[float]]) -> None:
        self._collection.add(
            ids=[d.id for d in docs],
            documents=[d.content for d in docs],
            embeddings=embeddings,
            metadatas=[{"source": d.source, **d.metadata} for d in docs],
        )

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        results = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
        search_results = []
        if results["documents"]:
            for i, doc_text in enumerate(results["documents"][0]):
                doc = Document(
                    id=results["ids"][0][i],
                    content=doc_text,
                    source=results["metadatas"][0][i].get("source", ""),
                )
                score = 1.0 - (results["distances"][0][i] if results["distances"] else 0)
                search_results.append(SearchResult(document=doc, score=score))
        return search_results

    async def delete(self, doc_ids: list[str]) -> None:
        self._collection.delete(ids=doc_ids)
