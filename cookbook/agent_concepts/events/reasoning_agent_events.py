import asyncio

from agno.agent import RunEvent
from agno.agent.agent import Agent
from agno.models.openai.chat import OpenAIChat

finance_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    reasoning=True,
)


async def run_agent_with_events(prompt: str):
    content_started = False
    async for run_response_event in await finance_agent.arun(
        prompt,
        stream=True,
        stream_intermediate_steps=True,
    ):
        if run_response_event.event in [RunEvent.run_started, RunEvent.run_completed]:
            print(f"\nEVENT: {run_response_event.event}")

        if run_response_event.event in [RunEvent.reasoning_started]:
            print(f"\nEVENT: {run_response_event.event}")

        if run_response_event.event in [RunEvent.reasoning_step]:
            print(f"\nEVENT: {run_response_event.event}")
            print(f"REASONING CONTENT: {run_response_event.reasoning_content}")

        if run_response_event.event in [RunEvent.reasoning_completed]:
            print(f"\nEVENT: {run_response_event.event}")

        if run_response_event.event in [RunEvent.run_response_content]:
            if not content_started:
                print("\nCONTENT:")
                content_started = True
            else:
                print(run_response_event.content, end="")


if __name__ == "__main__":
    task = (
        "Analyze the key factors that led to the signing of the Treaty of Versailles in 1919. "
        "Discuss the political, economic, and social impacts of the treaty on Germany and how it "
        "contributed to the onset of World War II. Provide a nuanced assessment that includes "
        "multiple historical perspectives."
    )
    asyncio.run(
        run_agent_with_events(
            task,
        )
    )
