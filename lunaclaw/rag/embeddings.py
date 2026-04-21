from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedding(EmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        import os

        from sentence_transformers import SentenceTransformer

        # Try local cache first, fall back to download
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        try:
            self._model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            self._model = SentenceTransformer(model_name)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts)
        return [e.tolist() for e in embeddings]
