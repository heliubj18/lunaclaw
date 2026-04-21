from __future__ import annotations

from pathlib import Path

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.rag.engine import RAGEngine
from lunaclaw.tools.base import BaseTool, ToolResult


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "Search the indexed knowledge base for relevant information"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }
    requires_approval = False

    def __init__(self, engine: RAGEngine) -> None:
        self._engine = engine

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        results = await self._engine.search(params["query"], top_k=params.get("top_k", 5))
        if not results:
            return ToolResult(success=True, output="No relevant documents found")
        lines = []
        for r in results:
            lines.append(f"[score={r.score:.2f}] (source: {r.document.source})")
            lines.append(r.document.content)
            lines.append("")
        return ToolResult(success=True, output="\n".join(lines).strip())


class RAGIngestTool(BaseTool):
    name = "rag_ingest"
    description = "Index a file or text into the knowledge base"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file to ingest"},
            "text": {"type": "string", "description": "Raw text to ingest (alternative to path)"},
            "source": {"type": "string", "description": "Source label for the content"},
        },
    }
    requires_approval = False

    def __init__(self, engine: RAGEngine) -> None:
        self._engine = engine

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        try:
            if "path" in params:
                count = await self._engine.ingest_file(Path(params["path"]))
                return ToolResult(
                    success=True, output=f"Ingested {count} chunks from {params['path']}"
                )
            elif "text" in params:
                count = await self._engine.ingest(
                    params["text"], source=params.get("source", "inline")
                )
                return ToolResult(success=True, output=f"Ingested {count} chunks")
            else:
                return ToolResult(success=False, error="Provide either 'path' or 'text'")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
