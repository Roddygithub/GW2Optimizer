"""Tests for Team API endpoints."""

import pytest
from httpx import AsyncClient
from fastapi import status


pytestmark = pytest.mark.asyncio


class TestTeamAPI:
    """Test suite for Team API endpoints."""

    async def test_create_team_unauthorized(self, client: AsyncClient):
        """Test that creating a team without auth fails."""
        team_data = {
            "name": "Test Team",
            "game_mode": "zerg",
            "team_size": 15,
        }

        response = await client.post("/api/v1/teams", json=team_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_team_authenticated(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test creating a team with authentication."""
        response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_team_data["name"]
        assert data["game_mode"] == sample_team_data["game_mode"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_team_with_builds(
        self, client: AsyncClient, auth_headers: dict, sample_team_data: dict, sample_build_data: dict
    ):
        """Test creating a team with builds."""
        # Create builds first
        build1_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build1_id = build1_response.json()["id"]

        sample_build_data["name"] = "Second Build"
        build2_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build2_id = build2_response.json()["id"]

        # Create team with builds
        sample_team_data["build_ids"] = [build1_id, build2_id]
        response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["slots"]) == 2

    async def test_get_team_by_id(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test getting a team by ID."""
        # Create a team first
        create_response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        team_id = create_response.json()["id"]

        # Get the team
        response = await client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == team_id
        assert data["name"] == sample_team_data["name"]

    async def test_get_nonexistent_team(self, client: AsyncClient, auth_headers: dict):
        """Test getting a team that doesn't exist."""
        response = await client.get("/api/v1/teams/nonexistent-id", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_user_teams(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test listing user's teams."""
        # Create multiple teams
        await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        sample_team_data["name"] = "Second Team"
        await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        # List teams
        response = await client.get("/api/v1/teams", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    async def test_list_public_teams(self, client: AsyncClient, sample_team_data: dict, auth_headers: dict):
        """Test listing public teams without authentication."""
        # Create a public team
        sample_team_data["is_public"] = True
        await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        # List public teams without auth
        response = await client.get("/api/v1/teams/public/all")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(team["is_public"] for team in data)

    async def test_update_team(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test updating a team."""
        # Create a team
        create_response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        team_id = create_response.json()["id"]

        # Update the team
        update_data = {
            "name": "Updated Team Name",
            "description": "Updated description",
        }

        response = await client.put(f"/api/v1/teams/{team_id}", json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Team Name"
        assert data["description"] == "Updated description"

    async def test_delete_team(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test deleting a team."""
        # Create a team
        create_response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        team_id = create_response.json()["id"]

        # Delete the team
        response = await client.delete(f"/api/v1/teams/{team_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify team is deleted
        get_response = await client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_add_build_to_team(
        self, client: AsyncClient, auth_headers: dict, sample_team_data: dict, sample_build_data: dict
    ):
        """Test adding a build to a team."""
        # Create a build
        build_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = build_response.json()["id"]

        # Create a team
        team_response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        team_id = team_response.json()["id"]

        # Add build to team
        response = await client.post(f"/api/v1/teams/{team_id}/builds/{build_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["slots"]) == 1
        assert data["slots"][0]["build"]["id"] == build_id

    async def test_remove_build_from_team(
        self, client: AsyncClient, auth_headers: dict, sample_team_data: dict, sample_build_data: dict
    ):
        """Test removing a build from a team."""
        # Create a build
        build_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = build_response.json()["id"]

        # Create a team with the build
        sample_team_data["build_ids"] = [build_id]
        team_response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        team_id = team_response.json()["id"]
        slot_id = team_response.json()["slots"][0]["id"]

        # Remove build from team
        response = await client.delete(f"/api/v1/teams/{team_id}/slots/{slot_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify slot was removed
        get_response = await client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)
        data = get_response.json()
        assert len(data["slots"]) == 0

    async def test_get_team_stats(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test getting team statistics."""
        # Create teams
        await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        sample_team_data["name"] = "Second Team"
        await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        # Get stats
        response = await client.get("/api/v1/teams/stats/count", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 2

    async def test_team_with_public_and_private_builds(
        self, client: AsyncClient, auth_headers: dict, sample_team_data: dict, sample_build_data: dict
    ):
        """Test creating a team with both public and private builds."""
        # Create a public build
        sample_build_data["is_public"] = True
        public_build_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        public_build_id = public_build_response.json()["id"]

        # Create a private build
        sample_build_data["name"] = "Private Build"
        sample_build_data["is_public"] = False
        private_build_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        private_build_id = private_build_response.json()["id"]

        # Create team with both builds
        sample_team_data["build_ids"] = [public_build_id, private_build_id]
        response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["slots"]) == 2
