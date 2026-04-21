import pytest
from lunaclaw.tools.shell import ShellTool
from lunaclaw.audit.tracer import TraceContext


@pytest.fixture
def shell():
    return ShellTool()


def test_shell_tool_metadata(shell):
    assert shell.name == "shell"
    assert shell.requires_approval is True
    assert "command" in shell.parameters["properties"]


@pytest.mark.asyncio
async def test_shell_echo(shell):
    trace = TraceContext()
    result = await shell.execute({"command": "echo hello"}, trace)
    assert result.success is True
    assert "hello" in result.output


@pytest.mark.asyncio
async def test_shell_failure(shell):
    trace = TraceContext()
    result = await shell.execute({"command": "false"}, trace)
    assert result.success is False


@pytest.mark.asyncio
async def test_shell_timeout(shell):
    trace = TraceContext()
    result = await shell.execute({"command": "sleep 60", "timeout": 1}, trace)
    assert result.success is False
    assert "timed out" in result.error.lower()
