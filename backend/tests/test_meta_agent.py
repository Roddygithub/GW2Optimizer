"""
Tests for Meta Agent

Tests unitaires pour le Meta Agent (analyse et adaptation de méta).
"""

import pytest

from app.agents.meta_agent import MetaAgent


@pytest.mark.asyncio
class TestMetaAgent:
    """Tests pour le Meta Agent."""

    async def test_meta_agent_initialization(self):
        """Test l'initialisation du Meta Agent."""
        agent = MetaAgent()

        assert agent.name == "MetaAgent"
        assert agent.version == "1.0.0"
        assert "meta_analysis" in agent.capabilities
        assert "trend_detection" in agent.capabilities
        assert agent.trend_threshold == 0.15

    async def test_meta_agent_run_zerg_mode(self):
        """Test l'exécution du Meta Agent en mode zerg."""
        agent = MetaAgent()
        await agent.initialize()

        result = await agent.execute({"game_mode": "zerg", "time_range": 30})

        assert result["success"] is True
        assert "result" in result

        meta_result = result["result"]
        assert "meta_snapshot" in meta_result
        assert "trends" in meta_result
        assert "recommendations" in meta_result
        assert "viability_scores" in meta_result
        assert "predictions" in meta_result

    async def test_meta_agent_with_profession(self):
        """Test l'analyse de méta pour une profession spécifique."""
        agent = MetaAgent()
        await agent.initialize()

        result = await agent.execute({"game_mode": "raid_guild", "profession": "Guardian", "time_range": 14})

        assert result["success"] is True
        meta_result = result["result"]

        assert meta_result["meta_snapshot"]["profession"] == "Guardian"
        assert meta_result["meta_snapshot"]["game_mode"] == "raid_guild"

    async def test_meta_agent_viability_scoring(self):
        """Test le calcul des scores de viabilité."""
        agent = MetaAgent()
        await agent.initialize()

        test_builds = [
            {"id": "build_1", "role": "support", "profession": "Guardian"},
            {"id": "build_2", "role": "dps", "profession": "Warrior"},
        ]

        result = await agent.execute({"game_mode": "zerg", "current_builds": test_builds, "time_range": 30})

        assert result["success"] is True
        viability_scores = result["result"]["viability_scores"]

        # Vérifier que les scores sont calculés
        assert "build_1" in viability_scores
        assert "build_2" in viability_scores

        # Vérifier que les scores sont dans la plage valide
        for score in viability_scores.values():
            assert 0.0 <= score <= 1.0

    async def test_meta_agent_recommendations(self):
        """Test la génération de recommandations."""
        agent = MetaAgent()
        await agent.initialize()

        result = await agent.execute({"game_mode": "roaming", "time_range": 30})

        assert result["success"] is True
        recommendations = result["result"]["recommendations"]

        # Vérifier la structure des recommandations
        assert isinstance(recommendations, list)

        if recommendations:
            rec = recommendations[0]
            assert "type" in rec
            assert "priority" in rec
            assert "description" in rec

    async def test_meta_agent_invalid_game_mode(self):
        """Test la validation du mode de jeu."""
        agent = MetaAgent()
        await agent.initialize()

        result = await agent.execute({"game_mode": "invalid_mode", "time_range": 30})

        assert result["success"] is False
        assert "error" in result

    async def test_meta_agent_invalid_time_range(self):
        """Test la validation de la période d'analyse."""
        agent = MetaAgent()
        await agent.initialize()

        # Time range trop court
        result = await agent.execute({"game_mode": "zerg", "time_range": 0})
        assert result["success"] is False

        # Time range trop long
        result = await agent.execute({"game_mode": "zerg", "time_range": 500})
        assert result["success"] is False

    async def test_meta_agent_trend_detection(self):
        """Test la détection de tendances."""
        agent = MetaAgent()
        await agent.initialize()

        result = await agent.execute({"game_mode": "zerg", "time_range": 60})

        assert result["success"] is True
        trends = result["result"]["trends"]

        assert isinstance(trends, list)

        if trends:
            trend = trends[0]
            assert "type" in trend
            assert "description" in trend
            assert "confidence" in trend
            assert 0.0 <= trend["confidence"] <= 1.0

    async def test_meta_agent_predictions(self):
        """Test les prédictions d'évolution du méta."""
        agent = MetaAgent()
        await agent.initialize()

        result = await agent.execute({"game_mode": "raid_guild", "time_range": 30})

        assert result["success"] is True
        predictions = result["result"]["predictions"]

        assert "timeframe" in predictions
        assert "confidence" in predictions
        assert "expected_changes" in predictions
        assert "risk_factors" in predictions
        assert isinstance(predictions["expected_changes"], list)
        assert isinstance(predictions["risk_factors"], list)

    async def test_meta_agent_cleanup(self):
        """Test le nettoyage du Meta Agent."""
        agent = MetaAgent()
        await agent.initialize()

        assert agent._is_initialized is True

        await agent.cleanup()

        assert agent._is_initialized is False
        assert len(agent.meta_history) == 0

    async def test_meta_agent_execution_count(self):
        """Test le compteur d'exécutions."""
        agent = MetaAgent()
        await agent.initialize()

        initial_count = agent.execution_count

        await agent.execute({"game_mode": "zerg", "time_range": 30})

        assert agent.execution_count == initial_count + 1
        assert agent.last_execution is not None

    async def test_meta_agent_get_info(self):
        """Test la récupération des informations de l'agent."""
        agent = MetaAgent()
        await agent.initialize()

        info = agent.get_info()

        assert info["name"] == "MetaAgent"
        assert info["version"] == "1.0.0"
        assert info["is_initialized"] is True
        assert "capabilities" in info
        assert len(info["capabilities"]) > 0
