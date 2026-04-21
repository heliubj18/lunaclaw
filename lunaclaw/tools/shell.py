from __future__ import annotations

import asyncio

from lunaclaw.audit.tracer import TraceContext
from lunaclaw.tools.base import BaseTool, ToolResult


class ShellTool(BaseTool):
    name = "shell"
    description = "Execute a shell command and return stdout/stderr"
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to execute"},
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 120)",
                "default": 120,
            },
        },
        "required": ["command"],
    }
    requires_approval = True

    async def execute(self, params: dict, trace: TraceContext) -> ToolResult:
        command = params["command"]
        timeout = params.get("timeout", 120)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        output = stdout.decode() if stdout else ""
        err_output = stderr.decode() if stderr else ""
        combined = output + ("\n" + err_output if err_output else "")

        return ToolResult(
            success=proc.returncode == 0,
            output=combined.strip(),
            error=err_output.strip() if proc.returncode != 0 else None,
        )
