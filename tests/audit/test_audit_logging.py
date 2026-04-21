import json
import pytest

from lunaclaw.audit.tracer import TraceContext, AuditLogger
from lunaclaw.audit.types import TraceEvent


@pytest.fixture
def logger(tmp_path):
    return AuditLogger(log_dir=tmp_path)


def test_audit_logger_saves_trace(logger, tmp_path):
    trace = TraceContext()
    trace.record(TraceEvent(event_type="user_input", data={"query": "test"}))
    trace.record(TraceEvent(event_type="final_output", data={"content": "done"}))

    logger.save(trace)

    log_files = list(tmp_path.glob("*.json"))
    assert len(log_files) == 1

    saved = json.loads(log_files[0].read_text())
    assert saved["trace_id"] == trace.trace_id
    assert len(saved["events"]) == 2


def test_audit_logger_lists_traces(logger, tmp_path):
    for i in range(3):
        trace = TraceContext()
        trace.record(TraceEvent(event_type="user_input", data={"query": f"test {i}"}))
        logger.save(trace)

    traces = logger.list_traces()
    assert len(traces) == 3


def test_audit_logger_load_trace(logger, tmp_path):
    trace = TraceContext()
    trace.record(TraceEvent(event_type="user_input", data={"query": "hello"}))
    logger.save(trace)

    loaded = logger.load(trace.trace_id)
    assert loaded is not None
    assert loaded["trace_id"] == trace.trace_id
