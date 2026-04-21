from __future__ import annotations

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.tools.base import BaseTool, ToolResult

from duckduckgo_search import DDGS


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web using DuckDuckGo and return results"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }
    requires_approval = False

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        query = params["query"]
        max_results = params.get("max_results", 5)

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return ToolResult(success=True, output="No results found")

            lines = []
            for r in results:
                lines.append(f"**{r.get('title', '')}**")
                lines.append(f"URL: {r.get('href', '')}")
                lines.append(f"{r.get('body', '')}")
                lines.append("")

            return ToolResult(success=True, output="\n".join(lines).strip())
        except Exception as e:
            return ToolResult(success=False, error=str(e))
