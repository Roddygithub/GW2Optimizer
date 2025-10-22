"""Test health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "GW2Optimizer API"


@pytest.mark.asyncio
@pytest.mark.legacy
@pytest.mark.skip(reason="Root endpoint (/) not implemented - returns 404. Use /api/v1/health instead")
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "GW2Optimizer API"
