import json
import pytest
from unittest.mock import AsyncMock

from lunaclaw.core.subagent import SubagentResult
from lunaclaw.core.planner import PlannerSubagent, PlanStep
from lunaclaw.core.config import Config
from lunaclaw.llm.provider import LLMProvider, LLMResponse
from lunaclaw.audit.tracer import TraceContext


def test_subagent_result():
    result = SubagentResult(output="done", data={"steps": []})
    assert result.output == "done"


def test_plan_step():
    step = PlanStep(description="Search for files", tool_hint="glob")
    assert step.description == "Search for files"
    assert step.tool_hint == "glob"


@pytest.mark.asyncio
async def test_planner_returns_steps():
    config = Config(model="test-model")
    provider = LLMProvider(config)

    steps_json = json.dumps(
        [
            {"description": "Find Python files", "tool_hint": "glob"},
            {"description": "Read the main file", "tool_hint": "file_read"},
        ]
    )

    mock_response = LLMResponse(
        content=steps_json,
        tool_calls=[],
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )

    provider.complete = AsyncMock(return_value=mock_response)

    planner = PlannerSubagent(provider)
    trace = TraceContext()
    result = await planner.run(
        messages=[{"role": "user", "content": "Find all Python files and read main.py"}],
        query="Find all Python files and read main.py",
        trace=trace,
    )

    assert len(result.steps) == 2
    assert result.steps[0].description == "Find Python files"
    assert result.steps[0].tool_hint == "glob"
    assert any(e.event_type == "subagent_spawn" for e in trace.events)


@pytest.mark.asyncio
async def test_planner_handles_invalid_json():
    config = Config(model="test-model")
    provider = LLMProvider(config)

    mock_response = LLMResponse(
        content="This is not valid JSON",
        tool_calls=[],
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )

    provider.complete = AsyncMock(return_value=mock_response)

    planner = PlannerSubagent(provider)
    trace = TraceContext()
    result = await planner.run(
        messages=[{"role": "user", "content": "do something"}],
        query="do something",
        trace=trace,
    )

    assert len(result.steps) == 1
    assert result.steps[0].tool_hint is None
