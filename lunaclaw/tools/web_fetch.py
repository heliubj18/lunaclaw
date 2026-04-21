from __future__ import annotations

import re

import httpx

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.tools.base import BaseTool, ToolResult


def _html_to_text(html: str) -> str:
    """Simple HTML to text extraction — strips tags, decodes entities."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&nbsp;", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "Fetch a URL and extract its text content"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch"},
            "max_length": {
                "type": "integer",
                "description": "Max characters to return (default 10000)",
                "default": 10000,
            },
        },
        "required": ["url"],
    }
    requires_approval = False

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        url = params["url"]
        max_length = params.get("max_length", 10000)

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                response = await client.get(url)

            if response.status_code != 200:
                return ToolResult(success=False, error=f"HTTP {response.status_code}")

            content_type = response.headers.get("content-type", "")
            if "html" in content_type:
                text = _html_to_text(response.text)
            else:
                text = response.text

            if len(text) > max_length:
                text = text[:max_length] + "\n\n[truncated]"

            return ToolResult(success=True, output=text)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
