"""Test learning system endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_learning_stats(client: AsyncClient):
    """Test getting learning statistics."""
    response = await client.get("/api/v1/learning/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_datapoints" in data
    assert "average_quality_score" in data


@pytest.mark.asyncio
async def test_get_finetuning_config(client: AsyncClient):
    """Test getting fine-tuning configuration."""
    response = await client.get("/api/v1/learning/config/finetuning")
    assert response.status_code == 200
    data = response.json()
    assert "min_datapoints" in data
    assert "min_quality_threshold" in data


@pytest.mark.asyncio
async def test_get_storage_config(client: AsyncClient):
    """Test getting storage configuration."""
    response = await client.get("/api/v1/learning/config/storage")
    assert response.status_code == 200
    data = response.json()
    assert "max_storage_gb" in data
    assert "compression_enabled" in data
