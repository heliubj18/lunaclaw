import pytest

from lunaclaw.rag.engine import RAGEngine, Document
from lunaclaw.rag.embeddings import EmbeddingProvider
from lunaclaw.rag.store import VectorStore, SearchResult


class FakeEmbedding(EmbeddingProvider):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(hash(t) % 100) / 100.0] * 8 for t in texts]


class FakeVectorStore(VectorStore):
    def __init__(self):
        self._docs: dict[str, tuple[Document, list[float]]] = {}

    async def add(self, docs: list[Document], embeddings: list[list[float]]) -> None:
        for doc, emb in zip(docs, embeddings):
            self._docs[doc.id] = (doc, emb)

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
        results = []
        for doc, emb in self._docs.values():
            results.append(SearchResult(document=doc, score=0.9))
        return results[:top_k]

    async def delete(self, doc_ids: list[str]) -> None:
        for did in doc_ids:
            self._docs.pop(did, None)


@pytest.fixture
def engine():
    return RAGEngine(embedding=FakeEmbedding(), store=FakeVectorStore())


@pytest.mark.asyncio
async def test_ingest_text(engine):
    count = await engine.ingest("Hello world. This is a test document.", source="test.txt")
    assert count > 0


@pytest.mark.asyncio
async def test_ingest_and_search(engine):
    await engine.ingest("Python is a programming language.", source="python.txt")
    results = await engine.search("programming")
    assert len(results) > 0
    assert "Python" in results[0].document.content


@pytest.mark.asyncio
async def test_ingest_file(engine, tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Machine learning is fascinating.")
    count = await engine.ingest_file(f)
    assert count > 0
    results = await engine.search("machine learning")
    assert len(results) > 0
