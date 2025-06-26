from enum import Enum

import pytest
from pydantic import BaseModel, Field

from agno.agent import Agent, RunResponse  # noqa
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools


def test_tool_use():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[YFinanceTools(cache_results=True)],
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response = agent.run("What is the current price of TSLA?")

    # Verify tool usage
    assert any(msg.tool_calls for msg in response.messages)
    assert response.content is not None


def test_tool_use_stream():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[YFinanceTools(cache_results=True)],
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response_stream = agent.run("What is the current price of TSLA?", stream=True, stream_intermediate_steps=True)

    responses = []
    tool_call_seen = False

    for chunk in response_stream:
        responses.append(chunk)

        # Check for ToolCallStartedEvent or ToolCallCompletedEvent
        if chunk.event in ["ToolCallStarted", "ToolCallCompleted"] and hasattr(chunk, "tool") and chunk.tool:
            if chunk.tool.tool_name:
                tool_call_seen = True

    assert len(responses) > 0
    assert tool_call_seen, "No tool calls observed in stream"


@pytest.mark.asyncio
async def test_async_tool_use():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[YFinanceTools(cache_results=True)],
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response = await agent.arun("What is the current price of TSLA?")

    # Verify tool usage
    assert any(msg.tool_calls for msg in response.messages if msg.role == "assistant")
    assert response.content is not None


@pytest.mark.asyncio
async def test_async_tool_use_stream():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[YFinanceTools(cache_results=True)],
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response_stream = await agent.arun(
        "What is the current price of TSLA?", stream=True, stream_intermediate_steps=True
    )

    responses = []
    tool_call_seen = False

    async for chunk in response_stream:
        responses.append(chunk)

        # Check for ToolCallStartedEvent or ToolCallCompletedEvent
        if chunk.event in ["ToolCallStarted", "ToolCallCompleted"] and hasattr(chunk, "tool") and chunk.tool:
            if chunk.tool.tool_name:
                tool_call_seen = True

    assert len(responses) > 0
    assert tool_call_seen, "No tool calls observed in stream"
    assert any("TSLA" in r.content for r in responses if r.content)


@pytest.mark.skip("The SDK does not yet support native structured output with tool use")
def test_tool_use_with_native_structured_outputs():
    class StockPrice(BaseModel):
        price: float = Field(..., description="The price of the stock")
        currency: str = Field(..., description="The currency of the stock")

    agent = Agent(
        model=Gemini(id="gemini-2.5-flash-preview-04-17"),
        tools=[YFinanceTools(cache_results=True)],
        markdown=True,
        response_model=StockPrice,
        telemetry=False,
        monitoring=False,
        delay_between_retries=5,
    )
    # Gemini does not support structured outputs for tool calls at this time
    response = agent.run("What is the current price of TSLA?")
    assert isinstance(response.content, StockPrice)
    assert response.content is not None
    assert response.content.price is not None
    assert response.content.currency is not None


def test_tool_use_with_json_structured_outputs():
    class StockPrice(BaseModel):
        price: float = Field(..., description="The price of the stock")
        currency: str = Field(..., description="The currency of the stock")

    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-001"),
        tools=[YFinanceTools(cache_results=True)],
        exponential_backoff=True,
        delay_between_retries=5,
        markdown=True,
        response_model=StockPrice,
        use_json_mode=True,
        telemetry=False,
        monitoring=False,
    )
    # Gemini does not support structured outputs for tool calls at this time
    response = agent.run("What is the current price of TSLA?")
    assert isinstance(response.content, StockPrice)
    assert response.content is not None
    assert response.content.price is not None
    assert response.content.currency is not None


def test_parallel_tool_calls():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[YFinanceTools(cache_results=True)],
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response = agent.run("What is the current price of TSLA and AAPL?")

    # Verify tool usage
    tool_calls = []
    for msg in response.messages:
        if msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
    assert len([call for call in tool_calls if call.get("type", "") == "function"]) >= 2  # Total of 2 tool calls made
    assert response.content is not None
    assert "TSLA" in response.content and "AAPL" in response.content


def test_multiple_tool_calls():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[YFinanceTools(cache_results=True), DuckDuckGoTools(cache_results=True)],
        markdown=True,
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response = agent.run("What is the current price of TSLA and what is the latest news about it?")

    # Verify tool usage
    tool_calls = []
    for msg in response.messages:
        if msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
    assert len([call for call in tool_calls if call.get("type", "") == "function"]) >= 2  # Total of 2 tool calls made
    assert response.content is not None
    assert "TSLA" in response.content


def test_grounding():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-001", grounding=True),
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response = agent.run("What is the weather in Tokyo?")

    assert response.content is not None
    assert response.tools == []
    assert response.citations is not None
    assert len(response.citations.urls) > 0
    assert response.citations.raw is not None


def test_grounding_stream():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-001", grounding=True),
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response_stream = agent.run("What is the weather in Tokyo?", stream=True)

    responses = []
    citations_found = False

    for chunk in response_stream:
        responses.append(chunk)
        if chunk.citations is not None and chunk.citations.urls:
            citations_found = True

    assert len(responses) > 0
    assert citations_found


def test_search_stream():
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-001", search=True),
        exponential_backoff=True,
        delay_between_retries=5,
        telemetry=False,
        monitoring=False,
    )

    response_stream = agent.run("What are the latest scientific studies about climate change from 2024?", stream=True)

    responses = []
    citations_found = False

    for chunk in response_stream:
        responses.append(chunk)
        if chunk.citations is not None and chunk.citations.urls:
            citations_found = True

    assert len(responses) > 0
    assert citations_found


def test_tool_use_with_enum():
    """A simple test for enum tool use."""

    class Color(str, Enum):
        RED = "red"
        BLUE = "blue"

    def get_color(color: Color) -> str:
        """Returns the chosen color."""
        return f"The color is {color.value}"

    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-lite-preview-02-05"),
        tools=[get_color],
        telemetry=False,
        monitoring=False,
    )
    response = agent.run("I want the color red.")

    assert any(msg.tool_calls for msg in response.messages)
    tool_calls = []
    for msg in response.messages:
        if msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
    assert tool_calls[0]["function"]["name"] == "get_color"
    assert '"color": "red"' in tool_calls[0]["function"]["arguments"]
    assert "red" in response.content
