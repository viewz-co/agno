import pytest
from pydantic import BaseModel, Field

from agno.agent import Agent, RunResponse
from agno.models.cerebras import CerebrasOpenAI


def _assert_metrics(response: RunResponse):
    input_tokens = response.metrics.get("input_tokens", [])
    output_tokens = response.metrics.get("output_tokens", [])
    total_tokens = response.metrics.get("total_tokens", [])

    assert sum(input_tokens) > 0
    assert sum(output_tokens) > 0
    assert sum(total_tokens) > 0
    assert sum(total_tokens) == sum(input_tokens) + sum(output_tokens)


def test_basic():
    agent = Agent(
        model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"), markdown=True, telemetry=False, monitoring=False
    )

    response: RunResponse = agent.run("Share a 2 sentence horror story")

    assert response.content is not None
    assert len(response.messages) == 3
    assert [m.role for m in response.messages] == ["system", "user", "assistant"]

    _assert_metrics(response)


def test_basic_stream():
    agent = Agent(
        model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"), markdown=True, telemetry=False, monitoring=False
    )

    response_stream = agent.run("Share a 2 sentence horror story", stream=True)

    # Verify it's an iterator
    assert hasattr(response_stream, "__iter__")

    responses = list(response_stream)
    assert len(responses) > 0
    for response in responses:
        assert response.content is not None

    _assert_metrics(agent.run_response)


@pytest.mark.asyncio
async def test_async_basic():
    agent = Agent(
        model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"), markdown=True, telemetry=False, monitoring=False
    )

    response = await agent.arun("Share a 2 sentence horror story")

    assert response.content is not None
    assert len(response.messages) == 3
    assert [m.role for m in response.messages] == ["system", "user", "assistant"]
    _assert_metrics(response)


@pytest.mark.asyncio
async def test_async_basic_stream():
    agent = Agent(
        model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"), markdown=True, telemetry=False, monitoring=False
    )

    response_stream = await agent.arun("Share a 2 sentence horror story", stream=True)

    async for response in response_stream:
        assert response.content is not None

    _assert_metrics(agent.run_response)


def test_with_memory():
    agent = Agent(
        model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"),
        add_history_to_messages=True,
        num_history_runs=5,
        markdown=True,
        telemetry=False,
        monitoring=False,
    )

    # First interaction
    response1 = agent.run("My name is John Smith")
    assert response1.content is not None

    # Second interaction should remember the name
    response2 = agent.run("What's my name?")
    assert "John Smith" in response2.content

    # Verify memories were created
    messages = agent.get_messages_for_session()
    assert len(messages) == 5
    assert [m.role for m in messages] == ["system", "user", "assistant", "user", "assistant"]

    # Test metrics structure and types
    _assert_metrics(response2)


def test_structured_output():
    class MovieScript(BaseModel):
        title: str = Field(..., description="Movie title")
        genre: str = Field(..., description="Movie genre")
        plot: str = Field(..., description="Brief plot summary")

    agent = Agent(
        model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"),
        response_model=MovieScript,
        telemetry=False,
        monitoring=False,
    )

    response = agent.run("Create a movie about time travel")

    # Verify structured output
    assert isinstance(response.content, MovieScript)
    assert response.content.title is not None
    assert response.content.genre is not None
    assert response.content.plot is not None
