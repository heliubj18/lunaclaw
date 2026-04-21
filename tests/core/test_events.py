from lunaclaw.core.events import (
    UserMessage,
    AssistantMessage,
    ToolResultEvent,
    EventStream,
)
from lunaclaw.core.context import ContextManager


def test_user_message():
    msg = UserMessage(content="hello")
    assert msg.role == "user"
    assert msg.to_message() == {"role": "user", "content": "hello"}


def test_assistant_message():
    msg = AssistantMessage(content="hi there")
    assert msg.role == "assistant"
    assert msg.to_message() == {"role": "assistant", "content": "hi there"}


def test_assistant_message_with_tool_calls():
    msg = AssistantMessage(
        content=None,
        tool_calls=[{"id": "1", "name": "shell", "arguments": '{"command": "ls"}'}],
    )
    result = msg.to_message()
    assert result["role"] == "assistant"
    assert result["tool_calls"] is not None


def test_tool_result_event():
    event = ToolResultEvent(tool_call_id="1", content="output")
    result = event.to_message()
    assert result["role"] == "tool"
    assert result["tool_call_id"] == "1"


def test_event_stream():
    stream = EventStream()
    stream.add(UserMessage(content="hello"))
    stream.add(AssistantMessage(content="hi"))
    messages = stream.to_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_context_manager_fits_window():
    cm = ContextManager(max_tokens=1000)
    stream = EventStream()
    for i in range(5):
        stream.add(UserMessage(content=f"message {i}"))
        stream.add(AssistantMessage(content=f"response {i}"))
    messages = cm.fit_to_window(stream.to_messages())
    assert len(messages) > 0
    assert len(messages) <= 10
