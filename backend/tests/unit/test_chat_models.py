"""Unit tests for chat models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.chat import MessageRole, ChatMessage, ChatRequest, ChatResponse, BuildSuggestion

# Test data
SAMPLE_BUILD = {
    "id": "test-build-123",
    "name": "Heal Firebrand",
    "profession": "Guardian",
    "role": "Heal/Support",
    "weapons": {"main_hand": "Axe", "off_hand": "Shield"},
    "traits": ["Honor", "Virtues", "Firebrand"],
    "skills": ["Mantra of Solace", "Mantra of Potence", "Mantra of Liberation"],
    "stats": {"Healing Power": 1500, "Concentration": 1000},
    "player_count": 1,
    "gw2skills_url": "https://gw2skills.net/editor/abc123",
}


def test_message_role_enum():
    """Test MessageRole enum values."""
    assert MessageRole.USER == "user"
    assert MessageRole.ASSISTANT == "assistant"
    assert MessageRole.SYSTEM == "system"


def test_chat_message_validation():
    """Test ChatMessage model validation."""
    # Valid message
    msg = ChatMessage(role=MessageRole.USER, content="Hello!")
    assert msg.role == "user"
    assert msg.content == "Hello!"

    # Invalid role
    with pytest.raises(ValueError):
        ChatMessage(role="invalid", content="test")

    # Empty content
    with pytest.raises(ValueError):
        ChatMessage(role=MessageRole.USER, content="   ")


def test_chat_request_validation():
    """Test ChatRequest model validation."""
    # Valid request
    req = ChatRequest(
        message="Test message", conversation_history=[{"role": "user", "content": "Hello!"}], version="1.0.0"
    )
    assert req.message == "Test message"
    assert len(req.conversation_history) == 1

    # Message too long
    with pytest.raises(ValueError):
        ChatRequest(message="x" * 2001, version="1.0.0")

    # Invalid history format
    with pytest.raises(ValueError):
        ChatRequest(message="Test", conversation_history=[{"invalid": "data"}], version="1.0.0")


def test_build_suggestion():
    """Test BuildSuggestion model."""
    build = BuildSuggestion(**SAMPLE_BUILD)
    assert build.name == "Heal Firebrand"
    assert build.profession == "Guardian"
    assert build.gw2skills_url == "https://gw2skills.net/editor/abc123"


def test_chat_response():
    """Test ChatResponse model."""
    response = ChatResponse(
        response="Test response",
        suggestions=["Suggestion 1", "Suggestion 2"],
        builds=[SAMPLE_BUILD],
        metadata={"key": "value"},
    )

    assert response.response == "Test response"
    assert len(response.suggestions) == 2
    assert len(response.builds) == 1
    assert response.builds[0].name == "Heal Firebrand"
    assert response.metadata["key"] == "value"


# Add more tests for edge cases and validation


def test_chat_message_with_timestamp():
    """Test ChatMessage with timestamp."""
    timestamp = datetime.utcnow().isoformat()
    msg = ChatMessage(role=MessageRole.ASSISTANT, content="Hello!", timestamp=timestamp)
    assert msg.timestamp == timestamp


@pytest.mark.parametrize(
    "url, is_valid",
    [
        ("not-a-url", False),
        ("http://example.com", False),
        ("https://gw2skills.net/editor/", False),  # Incomplete URL
        ("https://gw2skills.net/editor/abc123", True),
        ("http://gw2skills.net/editor/abc123", True),
        ("https://en.gw2skills.net/editor/abc123", True),
    ],
)
def test_gw2skills_url_validation(url, is_valid):
    """Test validation of GW2Skills URLs."""
    if is_valid:
        build = BuildSuggestion(gw2skills_url=url)
        assert build.gw2skills_url == url
    else:
        with pytest.raises(ValueError):
            BuildSuggestion(gw2skills_url=url)


def test_chat_request_with_context():
    """Test ChatRequest with context."""
    context = {"game_mode": "wvw", "party_size": 5}
    req = ChatRequest(message="Best build?", context=context, version="1.0.0")
    assert req.context == context
