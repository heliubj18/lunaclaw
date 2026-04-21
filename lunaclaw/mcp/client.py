from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod


class McpTransport(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def call(self, method: str, params: dict) -> dict: ...

    @abstractmethod
    async def close(self) -> None: ...


class StdioTransport(McpTransport):
    def __init__(
        self, command: str, args: list[str] | None = None, env: dict | None = None
    ) -> None:
        self._command = command
        self._args = args or []
        self._env = env
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0

    async def connect(self) -> None:
        self._process = await asyncio.create_subprocess_exec(
            self._command,
            *self._args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
        )

    async def call(self, method: str, params: dict) -> dict:
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Transport not connected")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        line = json.dumps(request) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

        response_line = await asyncio.wait_for(self._process.stdout.readline(), timeout=30)
        response = json.loads(response_line.decode())

        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")

        return response.get("result", {})

    async def close(self) -> None:
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None
