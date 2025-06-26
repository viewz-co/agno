import os
from pathlib import Path

import pytest

from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.lancedb.lance_db import LanceDb


@pytest.fixture
def setup_vector_db():
    """Setup a temporary vector DB for testing."""
    table_name = f"docx_test_{os.urandom(4).hex()}"
    vector_db = LanceDb(table_name=table_name, uri="tmp/lancedb")
    yield vector_db
    # Clean up after test
    vector_db.drop()


def get_filtered_data_dir():
    """Get the path to the filtered test data directory."""
    return Path(__file__).parent / "data" / "filters"


def prepare_knowledge_base(setup_vector_db):
    """Prepare a knowledge base with filtered data."""
    # Create knowledge base
    kb = PDFKnowledgeBase(vector_db=setup_vector_db)

    # Load documents with different user IDs and metadata
    kb.load_document(
        path=get_filtered_data_dir() / "cv_1.pdf",
        metadata={"user_id": "jordan_mitchell", "document_type": "cv", "experience_level": "entry"},
        recreate=True,
    )

    kb.load_document(
        path=get_filtered_data_dir() / "cv_2.pdf",
        metadata={"user_id": "taylor_brooks", "document_type": "cv", "experience_level": "mid"},
    )

    return kb


async def aprepare_knowledge_base(setup_vector_db):
    """Prepare a knowledge base with filtered data asynchronously."""
    # Create knowledge base
    kb = PDFKnowledgeBase(vector_db=setup_vector_db)

    # Load documents with different user IDs and metadata
    await kb.aload_document(
        path=get_filtered_data_dir() / "cv_1.pdf",
        metadata={"user_id": "jordan_mitchell", "document_type": "cv", "experience_level": "entry"},
        recreate=True,
    )

    await kb.aload_document(
        path=get_filtered_data_dir() / "cv_2.pdf",
        metadata={"user_id": "taylor_brooks", "document_type": "cv", "experience_level": "mid"},
    )

    return kb


def test_pdf_knowledge_base():
    vector_db = LanceDb(
        table_name="recipes",
        uri="tmp/lancedb",
    )

    # Create a knowledge base with the PDFs from the data/pdfs directory
    knowledge_base = PDFKnowledgeBase(
        path=str(Path(__file__).parent / "data"),
        vector_db=vector_db,
    )

    knowledge_base.load(recreate=True)

    assert vector_db.exists()

    assert vector_db.get_count() == 15

    # Create and use the agent
    agent = Agent(knowledge=knowledge_base)
    response = agent.run("Show me how to make Tom Kha Gai", markdown=True)

    tool_calls = []
    for msg in response.messages:
        if msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
    for call in tool_calls:
        if call.get("type", "") == "function":
            assert call["function"]["name"] == "search_knowledge_base"

    # Clean up
    vector_db.drop()


@pytest.mark.asyncio
async def test_pdf_knowledge_base_async():
    vector_db = LanceDb(
        table_name="recipes_async",
        uri="tmp/lancedb",
    )

    # Create knowledge base
    knowledge_base = PDFKnowledgeBase(
        path=str(Path(__file__).parent / "data"),
        vector_db=vector_db,
    )

    await knowledge_base.aload(recreate=True)

    assert await vector_db.async_exists()
    assert await vector_db.async_get_count() == 15

    # Create and use the agent
    agent = Agent(knowledge=knowledge_base)
    response = await agent.arun("What ingredients do I need for Tom Kha Gai?", markdown=True)

    tool_calls = []
    for msg in response.messages:
        if msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
    for call in tool_calls:
        if call.get("type", "") == "function":
            assert call["function"]["name"] == "search_knowledge_base"

    assert any(ingredient in response.content.lower() for ingredient in ["coconut", "chicken", "galangal"])

    # Clean up
    await vector_db.async_drop()


# for the one with new knowledge filter DX- filters at initialization
def test_text_knowledge_base_with_metadata_path(setup_vector_db):
    """Test loading text files with metadata using the new path structure."""
    kb = PDFKnowledgeBase(
        path=[
            {
                "path": str(get_filtered_data_dir() / "cv_1.pdf"),
                "metadata": {"user_id": "jordan_mitchell", "document_type": "cv", "experience_level": "entry"},
            },
            {
                "path": str(get_filtered_data_dir() / "cv_2.pdf"),
                "metadata": {"user_id": "taylor_brooks", "document_type": "cv", "experience_level": "mid"},
            },
        ],
        vector_db=setup_vector_db,
    )

    kb.load(recreate=True)

    # Verify documents were loaded with metadata
    agent = Agent(knowledge=kb)
    response = agent.run(
        "Tell me about Jordan Mitchell's experience?", knowledge_filters={"user_id": "jordan_mitchell"}, markdown=True
    )

    assert (
        "entry" in response.content.lower()
        or "junior" in response.content.lower()
        or "Jordan" in response.content.lower()
    )
    assert "senior developer" not in response.content.lower()


def test_knowledge_base_with_metadata_path_invalid_filter(setup_vector_db):
    """Test filtering docx knowledge base with invalid filters using the new path structure."""
    kb = PDFKnowledgeBase(
        path=[
            {
                "path": str(get_filtered_data_dir() / "cv_1.pdf"),
                "metadata": {"user_id": "jordan_mitchell", "document_type": "cv", "experience_level": "entry"},
            },
            {
                "path": str(get_filtered_data_dir() / "cv_2.pdf"),
                "metadata": {"user_id": "taylor_brooks", "document_type": "cv", "experience_level": "mid"},
            },
        ],
        vector_db=setup_vector_db,
    )

    kb.load(recreate=True)

    # Initialize agent with invalid filters
    agent = Agent(knowledge=kb, knowledge_filters={"nonexistent_filter": "value"})

    response = agent.run("Tell me about the candidate's experience?", markdown=True)
    response_content = response.content.lower()

    assert len(response_content) > 50

    # Check the tool calls to verify the invalid filter was not used
    tool_calls = []
    for msg in response.messages:
        if msg.tool_calls:
            tool_calls.extend(msg.tool_calls)

    function_calls = [
        call
        for call in tool_calls
        if call.get("type") == "function" and call["function"]["name"] == "search_knowledge_base"
    ]

    found_invalid_filters = False
    for call in function_calls:
        call_args = call["function"].get("arguments", "{}")
        if "nonexistent_filter" in call_args:
            found_invalid_filters = True

    assert not found_invalid_filters


# for the one with new knowledge filter DX- filters at load
def test_knowledge_base_with_valid_filter(setup_vector_db):
    """Test filtering knowledge base with valid filters."""
    kb = prepare_knowledge_base(setup_vector_db)

    # Initialize agent with filters for Jordan Mitchell
    agent = Agent(knowledge=kb, knowledge_filters={"user_id": "jordan_mitchell"})

    # Run a query that should only return results from Jordan Mitchell's CV
    response = agent.run("Tell me about the Jordan Mitchell's experience?", markdown=True)

    # Check response content to verify filtering worked
    response_content = response.content

    # Jordan Mitchell's CV should mention "software engineering intern"
    assert (
        "entry-level" in response_content.lower()
        or "junior" in response_content.lower()
        or "jordan mitchell" in response_content.lower()
    )

    # Should not mention Taylor Brooks' experience as "senior developer"
    assert "senior developer" not in response_content.lower()


def test_knowledge_base_with_run_level_filter(setup_vector_db):
    """Test filtering knowledge base with filters passed at run time."""
    kb = prepare_knowledge_base(setup_vector_db)

    # Initialize agent without filters
    agent = Agent(knowledge=kb)

    # Run a query with filters provided at run time
    response = agent.run(
        "Tell me about Jordan Mitchell experience?", knowledge_filters={"user_id": "jordan_mitchell"}, markdown=True
    )

    # Check response content to verify filtering worked
    response_content = response.content.lower()

    # Check that we have a response with actual content
    assert len(response_content) > 50

    # Should not mention Jordan Mitchell's experience
    assert any(term in response_content for term in ["jordan mitchell", "entry-level", "junior"])


def test_knowledge_base_filter_override(setup_vector_db):
    """Test that run-level filters override agent-level filters."""
    kb = prepare_knowledge_base(setup_vector_db)

    # Initialize agent with jordan_mitchell filter
    agent = Agent(knowledge=kb, knowledge_filters={"user_id": "taylor_brooks"})

    # Run a query with taylor_brooks filter - should override the agent filter
    response = agent.run(
        "Tell me about Jordan Mitchell's experience?", knowledge_filters={"user_id": "jordan_mitchell"}, markdown=True
    )

    # Check response content to verify filtering worked
    response_content = response.content.lower()

    # Check that we have a response with actual content
    assert len(response_content) > 50

    # Should  mention Jordan Mitchell's experience
    assert any(term in response_content for term in ["jordan mitchell", "entry-level", "intern", "junior"])

    # Taylor Brooks' CV should not be used instead of Jordan Mitchell's
    assert not any(term in response_content for term in ["taylor", "brooks", "senior", "developer", "mid level"])
