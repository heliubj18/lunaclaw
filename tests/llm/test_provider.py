import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from lunaclaw.llm.provider import LLMProvider
from lunaclaw.core.config import Config
from lunaclaw.audit.tracer import TraceContext


@pytest.fixture
def config():
    return Config(model="claude-sonnet-4-6")


@pytest.fixture
def provider(config):
    return LLMProvider(config)


def test_provider_init(provider):
    assert provider.model == "claude-sonnet-4-6"


def test_build_messages(provider):
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
    ]
    result = provider._build_messages(messages)
    assert result == messages


def test_build_tools_schema(provider):
    tools = [
        {
            "name": "shell",
            "description": "Run a shell command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        }
    ]
    result = provider._build_tools(tools)
    assert len(result) == 1
    assert result[0]["type"] == "function"
    assert result[0]["function"]["name"] == "shell"


@pytest.mark.asyncio
async def test_complete_calls_litellm(provider):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello!"
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    trace = TraceContext()

    with patch("lunaclaw.llm.provider.acompletion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response
        result = await provider.complete(
            messages=[{"role": "user", "content": "Hi"}],
            tools=[],
            trace=trace,
        )

    assert result.content == "Hello!"
    assert result.tool_calls == []
    assert len(trace.events) == 2  # llm_request + llm_response


@pytest.mark.asyncio
async def test_complete_with_env_overrides(config):
    config.env = {"ANTHROPIC_BASE_URL": "https://custom.api.com"}
    provider = LLMProvider(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hi"
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    trace = TraceContext()

    with patch("lunaclaw.llm.provider.acompletion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response
        with patch.dict("os.environ", config.env):
            await provider.complete(
                messages=[{"role": "user", "content": "Hi"}],
                tools=[],
                trace=trace,
            )
        mock_llm.assert_called_once()
