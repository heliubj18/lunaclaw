import json
import pytest
from unittest.mock import AsyncMock

from lunaclaw.core.agent import AgentLoop
from lunaclaw.core.config import Config
from lunaclaw.llm.provider import LLMProvider, LLMResponse
from lunaclaw.tools.registry import ToolRegistry
from lunaclaw.tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    name = "echo"
    description = "Echo back the input"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }
    requires_approval = False

    async def execute(self, params, trace):
        return ToolResult(success=True, output=params["text"])


@pytest.fixture
def config():
    return Config(model="test-model")


@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register(EchoTool())
    return reg


@pytest.fixture
def provider(config):
    return LLMProvider(config)


@pytest.mark.asyncio
async def test_agent_simple_response(config, registry, provider):
    """Agent returns a text response without tool calls."""
    provider.complete = AsyncMock(
        return_value=LLMResponse(
            content="Hello! How can I help?",
            tool_calls=[],
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
    )

    agent = AgentLoop(config=config, provider=provider, registry=registry)
    response = await agent.process("Hi there")

    assert response == "Hello! How can I help?"


@pytest.mark.asyncio
async def test_agent_with_tool_call(config, registry, provider):
    """Agent uses a tool and returns the final response."""
    tool_response = LLMResponse(
        content=None,
        tool_calls=[
            {
                "id": "call_1",
                "name": "echo",
                "arguments": json.dumps({"text": "hello world"}),
            }
        ],
        usage={"prompt_tokens": 10, "completion_tokens": 5},
    )
    final_response = LLMResponse(
        content="The echo returned: hello world",
        tool_calls=[],
        usage={"prompt_tokens": 20, "completion_tokens": 10},
    )
    provider.complete = AsyncMock(side_effect=[tool_response, final_response])

    agent = AgentLoop(config=config, provider=provider, registry=registry)
    response = await agent.process("Echo hello world")

    assert "hello world" in response


@pytest.mark.asyncio
async def test_agent_maintains_conversation(config, registry, provider):
    """Agent maintains conversation history across calls."""
    provider.complete = AsyncMock(
        return_value=LLMResponse(
            content="Response",
            tool_calls=[],
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
    )

    agent = AgentLoop(config=config, provider=provider, registry=registry)
    await agent.process("First message")
    await agent.process("Second message")

    second_call_messages = provider.complete.call_args_list[1][1]["messages"]
    assert len(second_call_messages) >= 3


@pytest.mark.asyncio
async def test_agent_max_iterations(config, registry, provider):
    """Agent stops after max iterations to prevent infinite loops."""
    provider.complete = AsyncMock(
        return_value=LLMResponse(
            content=None,
            tool_calls=[
                {
                    "id": "call_1",
                    "name": "echo",
                    "arguments": json.dumps({"text": "loop"}),
                }
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
    )

    agent = AgentLoop(config=config, provider=provider, registry=registry, max_iterations=3)
    response = await agent.process("Loop forever")

    assert "max iterations" in response.lower() or provider.complete.call_count <= 4
