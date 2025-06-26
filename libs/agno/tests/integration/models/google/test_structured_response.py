import enum
from typing import Dict, List

from pydantic import BaseModel, Field
from rich.pretty import pprint  # noqa

from agno.agent import Agent, RunResponse  # noqa
from agno.models.google import Gemini


class MovieScript(BaseModel):
    setting: str = Field(..., description="Provide a nice setting for a blockbuster movie.")
    ending: str = Field(
        ...,
        description="Ending of the movie. If not available, provide a happy ending.",
    )
    genre: str = Field(
        ...,
        description="Genre of the movie. If not available, select action, thriller or romantic comedy.",
    )
    name: str = Field(..., description="Give a name to this movie")
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(..., description="3 sentence storyline for the movie. Make it exciting!")
    rating: Dict[str, int] = Field(
        ...,
        description="Your own rating of the movie. 1 to 5. Return a dictionary with the keys 'story' and 'acting'.",
    )


def test_structured_response_with_dict_fields():
    structured_output_agent = Agent(
        model=Gemini(id="gemini-2.0-flash"),
        description="You help people write movie scripts.",
        response_model=MovieScript,
    )
    response = structured_output_agent.run("New York")
    assert response.content is not None
    assert isinstance(response.content.rating, Dict)
    assert isinstance(response.content.setting, str)
    assert isinstance(response.content.ending, str)
    assert isinstance(response.content.genre, str)
    assert isinstance(response.content.name, str)
    assert isinstance(response.content.characters, List)
    assert isinstance(response.content.storyline, str)


def test_structured_response_with_enum_fields():
    class Grade(enum.Enum):
        A_PLUS = "a+"
        A = "a"
        B = "b"
        C = "c"
        D = "d"
        F = "f"

    class Recipe(BaseModel):
        recipe_name: str
        rating: Grade

    structured_output_agent = Agent(
        model=Gemini(id="gemini-2.0-flash"),
        description="You help generate recipe names and ratings.",
        response_model=Recipe,
    )
    response = structured_output_agent.run("Generate a recipe name and rating.")
    assert response.content is not None
    assert isinstance(response.content.rating, Grade)
    assert isinstance(response.content.recipe_name, str)
