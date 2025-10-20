"""Tests for Build API endpoints."""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.models.user import UserDB


pytestmark = pytest.mark.asyncio


class TestBuildAPI:
    """Test suite for Build API endpoints."""

    async def test_create_build_unauthorized(self, client: AsyncClient):
        """Test that creating a build without auth fails."""
        build_data = {
            "name": "Test Build",
            "profession": "Guardian",
            "game_mode": "zerg",
            "role": "support",
        }

        response = await client.post("/api/v1/builds", json=build_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_build_authenticated(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test creating a build with authentication."""
        response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_build_data["name"]
        assert data["profession"] == sample_build_data["profession"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_build_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """Test creating a build with invalid data."""
        invalid_data = {
            "name": "Test",
            "profession": "InvalidProfession",
            "game_mode": "zerg",
        }

        response = await client.post("/api/v1/builds", json=invalid_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_build_by_id(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test getting a build by ID."""
        # Create a build first
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Get the build
        response = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == build_id
        assert data["name"] == sample_build_data["name"]

    async def test_get_nonexistent_build(self, client: AsyncClient, auth_headers: dict):
        """Test getting a build that doesn't exist."""
        response = await client.get("/api/v1/builds/nonexistent-id", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_user_builds(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test listing user's builds."""
        # Create multiple builds
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        sample_build_data["name"] = "Second Build"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # List builds
        response = await client.get("/api/v1/builds", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    async def test_list_builds_with_profession_filter(
        self, client: AsyncClient, auth_headers: dict, sample_build_data: dict
    ):
        """Test listing builds with profession filter."""
        # Create builds with different professions
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        sample_build_data["name"] = "Necro Build"
        sample_build_data["profession"] = "Necromancer"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # Filter by Guardian
        response = await client.get("/api/v1/builds?profession=Guardian", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["profession"] == "Guardian"

    async def test_list_public_builds(self, client: AsyncClient, sample_build_data: dict, auth_headers: dict):
        """Test listing public builds without authentication."""
        # Create a public build
        sample_build_data["is_public"] = True
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # List public builds without auth
        response = await client.get("/api/v1/builds/public/all")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(build["is_public"] for build in data)

    async def test_update_build(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test updating a build."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Update the build
        update_data = {
            "name": "Updated Build Name",
            "description": "Updated description",
        }

        response = await client.put(f"/api/v1/builds/{build_id}", json=update_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Build Name"
        assert data["description"] == "Updated description"

    async def test_update_build_unauthorized(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test updating a build without authentication."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Try to update without auth
        update_data = {"name": "Hacked Build"}

        response = await client.put(f"/api/v1/builds/{build_id}", json=update_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_build(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test deleting a build."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Delete the build
        response = await client.delete(f"/api/v1/builds/{build_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        # Verify build is deleted
        get_response = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_build_unauthorized(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test deleting a build without authentication."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Try to delete without auth
        response = await client.delete(f"/api/v1/builds/{build_id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_build_stats(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test getting build statistics."""
        # Create builds
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        sample_build_data["name"] = "Second Build"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # Get stats
        response = await client.get("/api/v1/builds/stats/count", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 2

    async def test_pagination(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test pagination of build listings."""
        # Create 5 builds
        for i in range(5):
            sample_build_data["name"] = f"Build {i}"
            await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # Get first page
        response1 = await client.get("/api/v1/builds?skip=0&limit=2", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK
        page1 = response1.json()
        assert len(page1) == 2

        # Get second page
        response2 = await client.get("/api/v1/builds?skip=2&limit=2", headers=auth_headers)
        assert response2.status_code == status.HTTP_200_OK
        page2 = response2.json()
        assert len(page2) == 2

        # Verify different builds
        assert page1[0]["id"] != page2[0]["id"]
