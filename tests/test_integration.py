import json
import pytest
from unittest.mock import AsyncMock

from lunaclaw.core.agent import AgentLoop
from lunaclaw.core.config import Config, load_config
from lunaclaw.llm.provider import LLMProvider, LLMResponse
from lunaclaw.memory.store import FileMemoryStore
from lunaclaw.tools.registry import ToolRegistry
from lunaclaw.tools.shell import ShellTool
from lunaclaw.tools.file_ops import FileReadTool, FileWriteTool, FileEditTool, GlobTool, GrepTool
from lunaclaw.tools.memory import MemoryReadTool, MemoryWriteTool, MemorySearchTool


@pytest.fixture
def full_setup(tmp_path):
    config = Config(model="test-model")
    provider = LLMProvider(config)
    memory_store = FileMemoryStore(data_dir=tmp_path / "memory")

    registry = ToolRegistry()
    registry.register(ShellTool())
    registry.register(FileReadTool())
    registry.register(FileWriteTool())
    registry.register(FileEditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
    registry.register(MemoryReadTool(memory_store))
    registry.register(MemoryWriteTool(memory_store))
    registry.register(MemorySearchTool(memory_store))

    agent = AgentLoop(config=config, provider=provider, registry=registry)
    agent.set_approval_callback(AsyncMock(return_value=True))

    return agent, provider, memory_store


@pytest.mark.asyncio
async def test_full_conversation_with_tool(full_setup):
    agent, provider, _ = full_setup

    provider.complete = AsyncMock(
        side_effect=[
            LLMResponse(
                content=None,
                tool_calls=[
                    {
                        "id": "c1",
                        "name": "shell",
                        "arguments": json.dumps({"command": "echo integration-test"}),
                    }
                ],
                usage={"prompt_tokens": 10, "completion_tokens": 5},
            ),
            LLMResponse(
                content="The command output was: integration-test",
                tool_calls=[],
                usage={"prompt_tokens": 20, "completion_tokens": 10},
            ),
        ]
    )

    response = await agent.process("Run echo integration-test")
    assert "integration-test" in response


@pytest.mark.asyncio
async def test_memory_round_trip(full_setup):
    agent, provider, memory_store = full_setup

    provider.complete = AsyncMock(
        side_effect=[
            LLMResponse(
                content=None,
                tool_calls=[
                    {
                        "id": "c1",
                        "name": "memory_write",
                        "arguments": json.dumps(
                            {"content": "User prefers Python", "category": "user"}
                        ),
                    }
                ],
                usage={"prompt_tokens": 10, "completion_tokens": 5},
            ),
            LLMResponse(
                content="I've saved that preference.",
                tool_calls=[],
                usage={"prompt_tokens": 20, "completion_tokens": 10},
            ),
        ]
    )

    await agent.process("Remember that I prefer Python")

    memories = await memory_store.list()
    assert len(memories) == 1
    assert "Python" in memories[0].content


@pytest.mark.asyncio
async def test_config_loads_defaults(tmp_path):
    import os
    from unittest.mock import patch

    with (
        patch("lunaclaw.core.config.CLAUDE_CONFIG_DIR", tmp_path / "no_claude"),
        patch("lunaclaw.core.config.CLAW_CONFIG_DIR", tmp_path / "no_claw"),
        patch("lunaclaw.core.config.LUNACLAW_USER_DIR", tmp_path / "no_luna"),
    ):
        old = os.environ.pop("ANTHROPIC_MODEL", None)
        config = load_config(project_dir=tmp_path)
        if old is not None:
            os.environ["ANTHROPIC_MODEL"] = old
    assert config.model == "claude-sonnet-4-6"
    assert config.rag.chunk_size == 512
