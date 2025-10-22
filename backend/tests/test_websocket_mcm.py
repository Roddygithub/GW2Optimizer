"""
Tests for WebSocket McM Analytics endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.legacy
def test_websocket_health_endpoint():
    """Test the WebSocket health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_connections" in data


@pytest.mark.asyncio
async def test_mcm_analytics_service():
    """Test the McMAnalyticsService."""
    from app.services.mcm_analytics import McMAnalyticsService

    service = McMAnalyticsService()

    # Test get_current_metrics
    metrics = await service.get_current_metrics()
    assert "active_zergs" in metrics
    assert "total_players" in metrics
    assert "objectives_held" in metrics

    # Test get_live_metrics
    live_metrics = await service.get_live_metrics()
    assert "zergs" in live_metrics
    assert "battles" in live_metrics
    assert "score" in live_metrics

    # Test get_zerg_analytics
    zerg_analytics = await service.get_zerg_analytics("zerg_1")
    assert zerg_analytics is not None
    assert "composition" in zerg_analytics
    assert "synergy_score" in zerg_analytics


@pytest.mark.asyncio
async def test_squad_recommendations():
    """Test squad composition recommendations."""
    from app.services.mcm_analytics import McMAnalyticsService

    service = McMAnalyticsService()
    current_comp = {"guardian": 4, "necromancer": 3}

    recommendations = await service.get_squad_recommendations(current_comp)
    assert "recommendations" in recommendations
    assert "optimal_composition" in recommendations
    assert recommendations["current_score"] < recommendations["potential_score"]


@pytest.mark.asyncio
async def test_objective_tracking():
    """Test objective capture tracking."""
    from app.services.mcm_analytics import McMAnalyticsService

    service = McMAnalyticsService()

    capture_data = await service.track_objective_captures("hills_1")
    assert "objective_id" in capture_data
    assert "capture_history" in capture_data
    assert "current_holder" in capture_data


@pytest.mark.asyncio
async def test_battle_analytics():
    """Test battle analytics."""
    from app.services.mcm_analytics import McMAnalyticsService

    service = McMAnalyticsService()

    battle_data = await service.get_battle_analytics("battle_1")
    assert battle_data is not None
    assert "participants" in battle_data
    assert "outcome_prediction" in battle_data


@pytest.mark.asyncio
async def test_commander_stats():
    """Test commander statistics."""
    from app.services.mcm_analytics import McMAnalyticsService

    service = McMAnalyticsService()

    commander_data = await service.get_commander_stats("commander_1")
    assert commander_data is not None
    assert "win_rate" in commander_data
    assert "average_squad_size" in commander_data
    assert 0 <= commander_data["win_rate"] <= 1
