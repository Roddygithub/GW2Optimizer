"""Tests for AIService and Agents using mocks."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.ai_service import AIService
from app.agents.recommender_agent import RecommenderAgent


# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def redis_client():
    """Mock redis client to avoid skipping tests when redis is down."""
    mock = AsyncMock()
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_ollama_response():
    """Returns a standardized mock response for Ollama."""
    return {
        "response": json.dumps({
            "build_name": "Mocked Firebrand",
            "description": "A mocked build for testing",
            "synergies": ["Might", "Quickness"],
            "strengths": ["Boon support"],
            "weaknesses": ["Low DPS"],
            "suggestions": ["Add more CC"],
            "overall_rating": 8.5,
            "optimized_composition": ["Guardian", "Necromancer"],
            "changes": []
        }),
        "created_at": "2023-01-01T00:00:00Z"
    }


class TestAIService:
    """Test suite for AIService."""

    async def test_initialization(self):
        """Test that AIService initializes agents and workflows correctly."""
        service = AIService()
        
        # Check registration before init
        assert "recommender" in service.agents
        assert "synergy" in service.agents
        assert "optimizer" in service.agents
        assert "build_optimization" in service.workflows
        
        assert service._is_initialized is False
        
        # Check initialization
        await service.initialize()
        assert service._is_initialized is True
        
        # Check cleanup
        await service.cleanup()
        assert service._is_initialized is False

    async def test_run_agent_recommender_mocked(self, mock_ollama_response):
        """Test running the recommender agent with a mocked LLM response."""
        # Create a mock response object
        mock_response = MagicMock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status.return_value = None

        # Patch httpx.AsyncClient BEFORE initializing service so agents get mocked clients
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance
            
            service = AIService()
            await service.initialize()
            
            # For agents that create their own persistent clients (like SynergyAgent),
            # we need to replace their post method directly
            for agent in service.agents.values():
                if hasattr(agent, "_client") and agent._client:
                    agent._client.post = AsyncMock(return_value=mock_response)
            
            result = await service.run_agent("recommender", {
                "profession": "Guardian",
                "role": "Support",
                "game_mode": "WvW"
            })

            assert result["success"] is True
            assert result["agent"] == "RecommenderAgent"
            data = result["result"]
            assert data["build_name"] == "Mocked Firebrand"
            assert "synergies" in data

    async def test_agent_failure_handling(self):
        """Test that agent failures are caught and handled gracefully."""
        # Patch to simulate network error BEFORE initializing service
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.side_effect = Exception("Network error")
            MockClient.return_value.__aenter__.return_value = mock_client_instance
            
            service = AIService()
            await service.initialize()
            
            # For agents that create their own persistent clients,
            # we need to replace their post method directly
            for agent in service.agents.values():
                if hasattr(agent, "_client") and agent._client:
                    agent._client.post = AsyncMock(side_effect=Exception("Network error"))

            result = await service.run_agent("recommender", {
                "profession": "Guardian",
                "role": "Support",
                "game_mode": "WvW"
            })

            assert result["success"] is False
            assert "Network error" in result["error"]

    async def test_execute_workflow_mocked(self, mock_ollama_response):
        """Test executing a full workflow with mocked agents."""
        # We need to mock calls for multiple agents (recommender, synergy, etc.)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status.return_value = None

        # Patch httpx BEFORE initializing service so all agents get mocked clients
        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance
            
            service = AIService()
            await service.initialize()
            
            # For agents that create their own persistent clients,
            # we need to replace their post method directly
            for agent in service.agents.values():
                if hasattr(agent, "_client") and agent._client:
                    agent._client.post = AsyncMock(return_value=mock_response)

            result = await service.execute_workflow("build_optimization", {
                "profession": "Guardian",
                "role": "Support",
                "game_mode": "WvW",
                "context": "Test context"
            })

            assert result["success"] is True
            assert result["workflow"] == "BuildOptimizationWorkflow"
            assert result["steps_executed"] > 0
            assert "primary_build" in result["result"]
