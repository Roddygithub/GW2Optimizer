"""API tests for team composition endpoints.

These tests focus on the database-backed /api/v1/teams routes and permissions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.models import UserDB


pytestmark = pytest.mark.asyncio


async def test_list_teams_empty(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/v1/teams should return 200 and an empty list when user has no teams."""
    response = await client.get("/api/v1/teams", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


async def test_create_and_get_team(
    client: AsyncClient,
    auth_headers: dict,
    sample_team_data: dict,
) -> None:
    """Create a team via the API, then list and fetch it by ID."""
    # Create team
    create_resp = await client.post("/api/v1/teams", headers=auth_headers, json=sample_team_data)
    assert create_resp.status_code == 201, create_resp.text

    created = create_resp.json()
    team_id = created["id"]

    # List teams for current user
    list_resp = await client.get("/api/v1/teams", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert isinstance(items, list)
    assert any(team["id"] == team_id for team in items)

    # Get team by ID
    get_resp = await client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)
    assert get_resp.status_code == 200

    fetched = get_resp.json()
    assert fetched["id"] == team_id
    assert fetched["name"] == sample_team_data["name"]
    assert fetched["team_size"] == sample_team_data["team_size"]


async def test_get_team_permission_private_returns_404_for_other_user(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
    sample_team_data: dict,
) -> None:
    """A private team owned by user A must not be visible to user B (404)."""
    # 1) User A creates a private team via API
    team_payload = dict(sample_team_data)
    team_payload["is_public"] = False

    create_resp = await client.post("/api/v1/teams", headers=auth_headers, json=team_payload)
    assert create_resp.status_code == 201, create_resp.text
    team_id = create_resp.json()["id"]

    # 2) Create a second user directly in the DB
    other_user = UserDB(
        email="other-team@example.com",
        username="otherteamuser",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    # 3) Generate JWT for user B
    other_token = create_access_token(subject=str(other_user.id))
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 4) User B tries to access team A -> should get 404
    resp = await client.get(f"/api/v1/teams/{team_id}", headers=other_headers)

    assert resp.status_code == 404
    body = resp.json()
    assert body.get("detail") == "Team not found"
