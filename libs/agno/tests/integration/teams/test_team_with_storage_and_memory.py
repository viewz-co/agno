import os
import tempfile
import uuid

import pytest

from agno.agent.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.anthropic.claude import Claude
from agno.models.openai.chat import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from agno.team.team import Team


@pytest.fixture
def temp_storage_db_file():
    """Create a temporary SQLite database file for team storage testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    yield db_path

    # Clean up the temporary file after the test
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_memory_db_file():
    """Create a temporary SQLite database file for memory testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    yield db_path

    # Clean up the temporary file after the test
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def team_storage(temp_storage_db_file):
    """Create a SQLite storage for team sessions."""
    # Use a unique table name for each test run
    table_name = f"team_sessions_{uuid.uuid4().hex[:8]}"
    storage = SqliteStorage(table_name=table_name, db_file=temp_storage_db_file, mode="team")
    storage.create()
    return storage


@pytest.fixture
def memory_db(temp_memory_db_file):
    """Create a SQLite memory database for testing."""
    db = SqliteMemoryDb(db_file=temp_memory_db_file)
    db.create()
    return db


@pytest.fixture
def memory(memory_db):
    """Create a Memory instance for testing."""
    return Memory(model=Claude(id="claude-3-5-sonnet-20241022"), db=memory_db)


@pytest.fixture
def route_team(team_storage, memory):
    """Create a route team with storage and memory for testing."""
    return Team(
        name="Route Team",
        mode="route",
        model=OpenAIChat(id="gpt-4o-mini"),
        members=[],
        storage=team_storage,
        memory=memory,
        enable_user_memories=True,
    )


@pytest.mark.asyncio
async def test_run_history_persistence(route_team, team_storage, memory):
    """Test that all runs within a session are persisted in storage."""
    user_id = "john@example.com"
    session_id = "session_123"
    num_turns = 5

    # Clear memory for this specific test case
    memory.clear()

    # Perform multiple turns
    conversation_messages = [
        "What's the weather like today?",
        "What about tomorrow?",
        "Any recommendations for indoor activities?",
        "Search for nearby museums.",
        "Which one has the best reviews?",
    ]

    assert len(conversation_messages) == num_turns

    for msg in conversation_messages:
        await route_team.arun(msg, user_id=user_id, session_id=session_id)

    # Verify the stored session data after all turns
    team_session = team_storage.read(session_id=session_id)

    stored_memory_data = team_session.memory
    assert stored_memory_data is not None, "Memory data not found in stored session."

    stored_runs = stored_memory_data["runs"]
    assert isinstance(stored_runs, list), "Stored runs data is not a list."

    first_user_message_content = stored_runs[0]["messages"][1]["content"]
    assert first_user_message_content == conversation_messages[0]


@pytest.mark.asyncio
async def test_run_session_summary(route_team, team_storage, memory):
    """Test that the session summary is persisted in storage."""
    session_id = "session_123"
    user_id = "john@example.com"

    # Enable session summaries
    route_team.enable_user_memories = False
    route_team.enable_session_summaries = True

    # Clear memory for this specific test case
    memory.clear()

    await route_team.arun("Where is New York?", user_id=user_id, session_id=session_id)

    assert route_team.get_session_summary(user_id=user_id, session_id=session_id).summary is not None

    team_session = team_storage.read(session_id=session_id)
    assert len(team_session.memory["summaries"][user_id][session_id]) > 0

    await route_team.arun("Where is Tokyo?", user_id=user_id, session_id=session_id)

    assert route_team.get_session_summary(user_id=user_id, session_id=session_id).summary is not None

    team_session = team_storage.read(session_id=session_id)
    assert len(team_session.memory["summaries"][user_id][session_id]) > 0


@pytest.mark.asyncio
async def test_multi_user_multi_session_route_team(route_team, team_storage, memory):
    """Test multi-user multi-session route team with storage and memory."""
    # Define user and session IDs
    user_1_id = "user_1@example.com"
    user_2_id = "user_2@example.com"
    user_3_id = "user_3@example.com"

    user_1_session_1_id = "user_1_session_1"
    user_1_session_2_id = "user_1_session_2"
    user_2_session_1_id = "user_2_session_1"
    user_3_session_1_id = "user_3_session_1"

    # Clear memory for this test
    memory.clear()

    # Team interaction with user 1 - Session 1
    await route_team.arun("What is the current stock price of AAPL?", user_id=user_1_id, session_id=user_1_session_1_id)
    await route_team.arun("What are the latest news about Apple?", user_id=user_1_id, session_id=user_1_session_1_id)

    # Team interaction with user 1 - Session 2
    await route_team.arun(
        "Compare the stock performance of AAPL with recent tech industry news",
        user_id=user_1_id,
        session_id=user_1_session_2_id,
    )

    # Team interaction with user 2
    await route_team.arun("What is the current stock price of MSFT?", user_id=user_2_id, session_id=user_2_session_1_id)
    await route_team.arun(
        "What are the latest news about Microsoft?", user_id=user_2_id, session_id=user_2_session_1_id
    )

    # Team interaction with user 3
    await route_team.arun(
        "What is the current stock price of GOOGL?", user_id=user_3_id, session_id=user_3_session_1_id
    )
    await route_team.arun("What are the latest news about Google?", user_id=user_3_id, session_id=user_3_session_1_id)

    # Continue the conversation with user 1
    await route_team.arun(
        "Based on the information you have, what stock would you recommend investing in?",
        user_id=user_1_id,
        session_id=user_1_session_1_id,
    )

    # Verify storage DB has the right sessions
    all_session_ids = team_storage.get_all_session_ids()
    assert len(all_session_ids) == 4  # 4 sessions total

    # Check that each user has the expected sessions
    user_1_sessions = team_storage.get_all_sessions(user_id=user_1_id)
    assert len(user_1_sessions) == 2
    assert user_1_session_1_id in [session.session_id for session in user_1_sessions]
    assert user_1_session_2_id in [session.session_id for session in user_1_sessions]

    user_2_sessions = team_storage.get_all_sessions(user_id=user_2_id)
    assert len(user_2_sessions) == 1
    assert user_2_session_1_id in [session.session_id for session in user_2_sessions]

    user_3_sessions = team_storage.get_all_sessions(user_id=user_3_id)
    assert len(user_3_sessions) == 1
    assert user_3_session_1_id in [session.session_id for session in user_3_sessions]


@pytest.mark.asyncio
async def test_correct_sessions_in_db(route_team, team_storage, agent_storage):
    """Test multi-user multi-session route team with storage and memory."""
    # Define user and session IDs
    user_id = "user_1@example.com"
    session_id = "session_123"

    route_team.mode = "coordinate"
    route_team.members = [
        Agent(
            name="Answers small questions",
            model=OpenAIChat(id="gpt-4o-mini"),
            storage=agent_storage,
        ),
        Agent(
            name="Answers big questions",
            model=OpenAIChat(id="gpt-4o-mini"),
            storage=agent_storage,
        ),
    ]

    # Should create a new team session and agent session
    await route_team.arun(
        "Ask a big and a small question to your member agents", user_id=user_id, session_id=session_id
    )

    team_sessions = team_storage.get_all_sessions(entity_id=route_team.team_id)
    assert len(team_sessions) == 1
    assert team_sessions[0].session_id == session_id
    assert team_sessions[0].user_id == user_id
    assert len(team_sessions[0].memory["runs"][0]["member_responses"]) == 2

    agent_sessions = agent_storage.get_all_sessions()
    # Single shared session for both agents
    assert len(agent_sessions) == 1
    assert agent_sessions[0].session_id == session_id
    assert agent_sessions[0].user_id == user_id
    assert len(agent_sessions[0].memory["runs"]) == 2
    assert agent_sessions[0].memory["runs"][0]["session_id"] == session_id
    assert agent_sessions[0].memory["runs"][1]["session_id"] == session_id
    assert agent_sessions[0].memory["runs"][0]["run_id"] != agent_sessions[0].memory["runs"][1]["run_id"]
