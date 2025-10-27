"""Test build endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_builds_empty(client: AsyncClient):
    """Test listing builds when none exist."""
    response = await client.get("/api/v1/builds")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_nonexistent_build(client: AsyncClient):
    """Test getting a build that doesn't exist."""
    response = await client.get("/api/v1/builds/nonexistent")
    assert response.status_code == 401
