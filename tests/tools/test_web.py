import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from lunaclaw.tools.web_search import WebSearchTool
from lunaclaw.tools.web_fetch import WebFetchTool
from lunaclaw.audit.tracer import TraceContext


@pytest.fixture
def trace():
    return TraceContext()


# WebSearch
def test_web_search_metadata():
    tool = WebSearchTool()
    assert tool.name == "web_search"
    assert tool.requires_approval is False


@pytest.mark.asyncio
async def test_web_search(trace):
    tool = WebSearchTool()
    mock_results = [
        {"title": "Result 1", "href": "https://example.com", "body": "Example body"},
        {"title": "Result 2", "href": "https://example2.com", "body": "Another result"},
    ]
    with patch("lunaclaw.tools.web_search.DDGS") as MockDDGS:
        mock_instance = MagicMock()
        mock_instance.text.return_value = mock_results
        MockDDGS.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockDDGS.return_value.__exit__ = MagicMock(return_value=False)
        result = await tool.execute({"query": "test query"}, trace)

    assert result.success is True
    assert "Result 1" in result.output
    assert "example.com" in result.output


# WebFetch
def test_web_fetch_metadata():
    tool = WebFetchTool()
    assert tool.name == "web_fetch"
    assert tool.requires_approval is False


@pytest.mark.asyncio
async def test_web_fetch(trace):
    tool = WebFetchTool()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    mock_response.headers = {"content-type": "text/html"}

    with patch("lunaclaw.tools.web_fetch.httpx.AsyncClient") as MockClient:
        client_instance = AsyncMock()
        client_instance.get.return_value = mock_response
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = client_instance
        result = await tool.execute({"url": "https://example.com"}, trace)

    assert result.success is True
    assert "Hello world" in result.output
