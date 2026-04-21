from lunaclaw.audit.types import TraceEvent
from lunaclaw.audit.tracer import TraceContext


def test_trace_context_creates_with_id():
    trace = TraceContext()
    assert trace.trace_id is not None
    assert len(trace.events) == 0


def test_record_event():
    trace = TraceContext()
    event = TraceEvent(
        event_type="user_input",
        data={"query": "hello"},
    )
    trace.record(event)
    assert len(trace.events) == 1
    assert trace.events[0].event_type == "user_input"
    assert trace.events[0].timestamp is not None


def test_record_event_with_parent():
    trace = TraceContext()
    parent = TraceEvent(event_type="llm_request", data={"model": "test"})
    trace.record(parent)
    child = TraceEvent(
        event_type="tool_call",
        data={"tool": "shell"},
        parent_id=parent.event_id,
    )
    trace.record(child)
    assert trace.events[1].parent_id == parent.event_id


def test_to_json():
    trace = TraceContext()
    trace.record(TraceEvent(event_type="user_input", data={"query": "test"}))
    result = trace.to_json()
    assert "trace_id" in result
    assert "events" in result
    assert len(result["events"]) == 1
    assert result["events"][0]["event_type"] == "user_input"


def test_summary():
    trace = TraceContext()
    trace.record(TraceEvent(event_type="user_input", data={"query": "test"}))
    trace.record(TraceEvent(event_type="final_output", data={"content": "done"}))
    summary = trace.summary()
    assert "user_input" in summary
    assert "final_output" in summary
