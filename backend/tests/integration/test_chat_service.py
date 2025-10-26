"""Integration tests for the chat service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.models.chat import ChatRequest, MessageRole, ChatMessage
from app.services.ai.chat_service import ChatService

# Removed unused CircuitBreakerError import


class TestChatServiceIntegration:
    """Integration tests for ChatService with external dependencies."""

    @pytest.fixture
    def chat_service(self):
        """Create a ChatService instance with a mocked Ollama service."""
        service = ChatService()
        service.ollama = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_process_message_success(self, chat_service):
        """Test successful message processing."""
        # Mock the Ollama response
        chat_service.ollama.chat.return_value = (
            "This is a test response with some suggestions.\n- Suggestion 1\n- Suggestion 2"
        )

        # Create a test request
        request = ChatRequest(message="What's the best build for WvW?", conversation_history=[], version="1.0.0")

        # Process the message
        response = await chat_service.process_message(request)

        # Verify the response
        assert "test response" in response.response.lower()
        assert len(response.suggestions) >= 2  # Should extract at least 2 suggestions
        assert "suggestion 1" in [s.lower() for s in response.suggestions]
        assert isinstance(response.metadata, dict)
        assert "model_used" in response.metadata
        assert "tokens_generated" in response.metadata

    @pytest.mark.asyncio
    async def test_process_message_with_gw2skill_url(self, chat_service):
        """Test message processing with a GW2Skill URL."""
        # Mock the Ollama response
        chat_service.ollama.chat.return_value = "Analyzing your build..."

        # Create a test request with a GW2Skill URL
        request = ChatRequest(
            message="What do you think of this build? https://gw2skills.net/editor/abc123",
            conversation_history=[],
            version="1.0.0",
        )

        # Process the message
        response = await chat_service.process_message(request)

        # Verify the response includes build information
        assert len(response.builds) == 1
        assert "gw2skills.net" in response.builds[0].gw2skills_url
        assert response.action_required == "parse_build"

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, chat_service):
        """Test circuit breaker integration with the chat service."""
        # Make the ollama service fail
        chat_service.ollama.chat.side_effect = Exception("Service unavailable")

        # First request should fail but keep circuit closed
        request = ChatRequest(message="Test", version="1.0.0")

        # The circuit breaker should handle the error
        response = await chat_service.process_message(request)
        assert "error" in response.response.lower() or "unavailable" in response.response.lower()

        # After multiple failures, the circuit should open
        # We need to use a new chat service with a lower failure threshold
        from app.services.ai.chat_service import ChatService
        from app.core.circuit_breaker import CircuitBreaker

        # Create a new service with a circuit breaker that opens after 2 failures
        test_service = ChatService()
        test_service.ollama = AsyncMock()
        test_service.ollama.chat.side_effect = Exception("Service unavailable")

        # Replace the module-level breaker temporarily
        test_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        test_service.breaker = test_breaker
        test_service.circuit_breaker = test_breaker

        try:
            # First failure
            response = await test_service.process_message(request)
            assert "error" in response.response.lower() or "unavailable" in response.response.lower()

            # Second failure should report circuit open via response metadata
            response = await test_service.process_message(request)
            assert response.metadata.get("error") == "service_unavailable"
            assert response.metadata.get("circuit_state") == "OPEN"
        finally:
            test_breaker.reset()

    @pytest.mark.asyncio
    async def test_suggestion_extraction(self, chat_service):
        """Test extraction of suggestions from AI response."""
        test_response = """
        Here are some suggestions:
        1. Try a different weapon set
        2. Consider changing your traits
        • Use more defensive utilities
        * Focus on boon uptime
        """

        chat_service.ollama.chat.return_value = test_response

        request = ChatRequest(message="Suggest improvements", version="1.0.0")
        response = await chat_service.process_message(request)

        # Should extract all bullet points
        assert len(response.suggestions) == 4
        assert "weapon" in response.suggestions[0].lower()
        assert "traits" in response.suggestions[1].lower()

    @pytest.mark.asyncio
    async def test_conversation_history(self, chat_service):
        """Test handling of conversation history."""
        chat_service.ollama.chat.return_value = "I remember our conversation."

        history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]

        request = ChatRequest(message="Do you remember me?", conversation_history=history, version="1.0.0")

        await chat_service.process_message(request)

        # Verify the chat method was called with the full history
        args, kwargs = chat_service.ollama.chat.call_args
        messages = kwargs.get("messages", [])

        # Should include system prompt + history + current message
        assert len(messages) >= 3  # system + history + current
        assert any(msg["role"] == "system" for msg in messages)
        assert any(msg["content"] == "Hello" for msg in messages)
        assert any("remember" in msg["content"] for msg in messages if msg["role"] == "user")

    @pytest.mark.asyncio
    async def test_error_handling(self, chat_service):
        """Test error handling in the chat service."""
        # Test with invalid message (too long)
        with pytest.raises(ValueError):
            request = ChatRequest(message="x" * 2001, version="1.0.0")  # Exceeds MAX_MESSAGE_LENGTH
            await chat_service.process_message(request)

        # Test with invalid conversation history
        with pytest.raises(ValueError):
            request = ChatRequest(message="Test", conversation_history=[{"invalid": "data"}], version="1.0.0")
            await chat_service.process_message(request)
