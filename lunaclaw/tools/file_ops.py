from __future__ import annotations

import re
from pathlib import Path

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.tools.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    name = "file_read"
    description = "Read the contents of a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "offset": {"type": "integer", "description": "Line number to start from (0-based)"},
            "limit": {"type": "integer", "description": "Max number of lines to read"},
        },
        "required": ["path"],
    }
    requires_approval = False

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        path = Path(params["path"])
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        if not path.is_file():
            return ToolResult(success=False, error=f"Not a file: {path}")
        try:
            lines = path.read_text().splitlines(keepends=True)
            offset = params.get("offset", 0)
            limit = params.get("limit", len(lines))
            selected = lines[offset : offset + limit]
            numbered = [f"{i + offset + 1}\t{line}" for i, line in enumerate(selected)]
            return ToolResult(success=True, output="".join(numbered))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "Write content to a file (creates or overwrites)"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    }
    requires_approval = True

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        path = Path(params["path"])
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params["content"])
            return ToolResult(success=True, output=f"Written to {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileEditTool(BaseTool):
    name = "file_edit"
    description = "Replace a string in a file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "old_string": {"type": "string", "description": "The exact string to find"},
            "new_string": {"type": "string", "description": "The replacement string"},
        },
        "required": ["path", "old_string", "new_string"],
    }
    requires_approval = True

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        path = Path(params["path"])
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        content = path.read_text()
        if params["old_string"] not in content:
            return ToolResult(success=False, error="old_string not found in file")
        new_content = content.replace(params["old_string"], params["new_string"], 1)
        path.write_text(new_content)
        return ToolResult(success=True, output=f"Edited {path}")


class GlobTool(BaseTool):
    name = "glob"
    description = "Find files matching a glob pattern"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
            "path": {"type": "string", "description": "Directory to search in"},
        },
        "required": ["pattern"],
    }
    requires_approval = False

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        base = Path(params.get("path", "."))
        matches = sorted(base.glob(params["pattern"]))
        output = "\n".join(str(m) for m in matches[:200])
        return ToolResult(success=True, output=output or "No matches found")


class GrepTool(BaseTool):
    name = "grep"
    description = "Search file contents for a regex pattern"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "File or directory to search in"},
            "glob": {"type": "string", "description": "File glob filter (e.g. *.py)"},
        },
        "required": ["pattern"],
    }
    requires_approval = False

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        base = Path(params.get("path", "."))
        regex = re.compile(params["pattern"])
        glob_filter = params.get("glob", "**/*")
        results: list[str] = []

        if base.is_file():
            files = [base]
        else:
            files = [f for f in base.glob(glob_filter) if f.is_file()]

        for f in files[:100]:
            try:
                for i, line in enumerate(f.read_text().splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{f}:{i}: {line}")
            except (UnicodeDecodeError, PermissionError):
                continue

        return ToolResult(
            success=True,
            output="\n".join(results[:200]) or "No matches found",
        )
