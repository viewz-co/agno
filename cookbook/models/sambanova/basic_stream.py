from agno.agent import Agent, RunResponseEvent  # noqa
from agno.models.sambanova import Sambanova

agent = Agent(model=Sambanova(id="Meta-Llama-3.1-8B-Instruct"), markdown=True)

# Get the response in a variable
# run_response: Iterator[RunResponseEvent] = agent.run("Share a 2 sentence horror story", stream=True)
# for chunk in run_response:
#     print(chunk.content)

# Print the response in the terminal
agent.print_response("Share a 2 sentence horror story", stream=True)
