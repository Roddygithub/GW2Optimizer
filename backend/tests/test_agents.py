"""Tests for AI Agents."""

import pytest
from app.agents.recommender_agent import RecommenderAgent
from app.agents.synergy_agent import SynergyAgent
from app.agents.optimizer_agent import OptimizerAgent

pytestmark = pytest.mark.asyncio


class TestRecommenderAgent:
    """Tests for RecommenderAgent."""

    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = RecommenderAgent()
        assert agent.name == "RecommenderAgent"
        assert "build_recommendation" in agent.capabilities

    async def test_input_validation_success(self):
        """Test input validation passes with valid data."""
        agent = RecommenderAgent()
        inputs = {"profession": "Guardian", "role": "Support", "game_mode": "WvW"}
        await agent.validate_inputs(inputs)

    async def test_input_validation_missing_field(self):
        """Test input validation fails with missing field."""
        agent = RecommenderAgent()
        inputs = {"profession": "Guardian"}

        with pytest.raises(ValueError, match="Missing required fields"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_profession(self):
        """Test input validation fails with invalid profession."""
        agent = RecommenderAgent()
        inputs = {"profession": "InvalidClass", "role": "Support", "game_mode": "WvW"}

        with pytest.raises(ValueError, match="Invalid profession"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_role(self):
        """Test input validation fails with invalid role."""
        agent = RecommenderAgent()
        inputs = {"profession": "Guardian", "role": "InvalidRole", "game_mode": "WvW"}

        with pytest.raises(ValueError, match="Invalid role"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_game_mode(self):
        """Test input validation fails with invalid game mode."""
        agent = RecommenderAgent()
        inputs = {"profession": "Guardian", "role": "Support", "game_mode": "InvalidMode"}

        with pytest.raises(ValueError, match="Invalid game_mode"):
            await agent.validate_inputs(inputs)


class TestSynergyAgent:
    """Tests for SynergyAgent."""

    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = SynergyAgent()
        assert agent.name == "SynergyAgent"
        assert "team_composition_analysis" in agent.capabilities

    async def test_input_validation_success(self):
        """Test input validation passes with valid data."""
        agent = SynergyAgent()
        inputs = {"professions": ["Guardian", "Warrior", "Mesmer"], "game_mode": "WvW"}
        await agent.validate_inputs(inputs)

    async def test_input_validation_too_few_professions(self):
        """Test input validation fails with too few professions."""
        agent = SynergyAgent()
        inputs = {"professions": ["Guardian"], "game_mode": "WvW"}

        with pytest.raises(ValueError, match="at least 2 professions"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_too_many_professions(self):
        """Test input validation fails with too many professions."""
        agent = SynergyAgent()
        inputs = {"professions": ["Guardian"] * 51, "game_mode": "WvW"}

        with pytest.raises(ValueError, match="maximum of 50 professions"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_profession_in_list(self):
        """Test input validation fails with invalid profession in list."""
        agent = SynergyAgent()
        inputs = {"professions": ["Guardian", "InvalidClass", "Warrior"], "game_mode": "WvW"}

        with pytest.raises(ValueError, match="Invalid profession"):
            await agent.validate_inputs(inputs)


class TestOptimizerAgent:
    """Tests for OptimizerAgent."""

    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = OptimizerAgent()
        assert agent.name == "OptimizerAgent"
        assert "composition_optimization" in agent.capabilities

    async def test_input_validation_success(self):
        """Test input validation passes with valid data."""
        agent = OptimizerAgent()
        inputs = {
            "current_composition": ["Guardian", "Warrior"],
            "objectives": ["maximize_boons"],
            "game_mode": "Raids",
        }
        await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_objective(self):
        """Test input validation fails with invalid objective."""
        agent = OptimizerAgent()
        inputs = {
            "current_composition": ["Guardian", "Warrior"],
            "objectives": ["invalid_objective"],
            "game_mode": "Raids",
        }

        with pytest.raises(ValueError, match="Invalid objective"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_empty_composition(self):
        """Test input validation fails with empty composition."""
        agent = OptimizerAgent()
        inputs = {"current_composition": [], "objectives": ["maximize_boons"], "game_mode": "Raids"}

        with pytest.raises(ValueError, match="at least 1 profession"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_max_changes_too_high(self):
        """Test input validation fails with max_changes too high."""
        agent = OptimizerAgent()
        inputs = {
            "current_composition": ["Guardian", "Warrior"],
            "objectives": ["maximize_boons"],
            "game_mode": "Raids",
            "max_changes": 20,
        }

        with pytest.raises(ValueError, match="max_changes must be between"):
            await agent.validate_inputs(inputs)
