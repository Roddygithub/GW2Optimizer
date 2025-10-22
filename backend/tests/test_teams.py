"""Test team endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.legacy
@pytest.mark.skip(reason="Requires authentication - endpoint protected. Use test_api/test_teams.py instead")
async def test_list_teams_empty(client: AsyncClient):
    """Test listing teams when none exist."""
    response = await client.get("/api/v1/teams")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
@pytest.mark.legacy
@pytest.mark.skip(reason="Requires authentication - endpoint protected. Use test_api/test_teams.py instead")
async def test_get_nonexistent_team(client: AsyncClient):
    """Test getting a team that doesn't exist."""
    response = await client.get("/api/v1/teams/nonexistent")
    assert response.status_code == 404
