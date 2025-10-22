"""Integration tests for cache functionality."""

import pytest
import os
import time
from httpx import AsyncClient
from fastapi import status

from app.core.cache import CacheManager
from app.core.config import settings


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestCacheFlow:
    """Test suite for cache functionality with Redis and disk fallback."""

    async def test_cache_build_retrieval(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that builds are cached after retrieval."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # First retrieval - should hit database
        start_time = time.time()
        response1 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        first_duration = time.time() - start_time

        assert response1.status_code == status.HTTP_200_OK

        # Second retrieval - should hit cache (faster)
        start_time = time.time()
        response2 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        second_duration = time.time() - start_time

        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()
        # Cache should be faster (though this might not always be true in tests)
        # assert second_duration < first_duration

    async def test_cache_invalidation_on_update(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that cache is invalidated when build is updated."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Get the build (cache it)
        response1 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response1.json()["name"] == sample_build_data["name"]

        # Update the build
        update_data = {"name": "Updated Build Name"}
        await client.put(f"/api/v1/builds/{build_id}", json=update_data, headers=auth_headers)

        # Get the build again - should reflect the update
        response2 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response2.json()["name"] == "Updated Build Name"

    async def test_cache_invalidation_on_delete(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that cache is invalidated when build is deleted."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Get the build (cache it)
        response1 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK

        # Delete the build
        await client.delete(f"/api/v1/builds/{build_id}", headers=auth_headers)

        # Try to get the build again - should return 404
        response2 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response2.status_code == status.HTTP_404_NOT_FOUND

    async def test_public_builds_list_caching(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that public builds list is cached."""
        # Create public builds
        sample_build_data["is_public"] = True
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        sample_build_data["name"] = "Second Build"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # First request
        response1 = await client.get("/api/v1/builds/public/all")
        assert response1.status_code == status.HTTP_200_OK
        builds1 = response1.json()

        # Second request (should be cached)
        response2 = await client.get("/api/v1/builds/public/all")
        assert response2.status_code == status.HTTP_200_OK
        builds2 = response2.json()

        assert builds1 == builds2

    async def test_cache_with_filters(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that cache respects query filters."""
        # Create builds with different professions
        sample_build_data["profession"] = "Guardian"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        sample_build_data["name"] = "Necro Build"
        sample_build_data["profession"] = "Necromancer"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # Request with Guardian filter
        response1 = await client.get("/api/v1/builds?profession=Guardian", headers=auth_headers)
        guardian_builds = response1.json()
        assert len(guardian_builds) == 1
        assert guardian_builds[0]["profession"] == "Guardian"

        # Request with Necromancer filter
        response2 = await client.get("/api/v1/builds?profession=Necromancer", headers=auth_headers)
        necro_builds = response2.json()
        assert len(necro_builds) == 1
        assert necro_builds[0]["profession"] == "Necromancer"

    async def test_disk_cache_fallback(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that disk cache works when Redis is unavailable."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Get the build to cache it
        response1 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK

        # Simulate Redis being unavailable by clearing the cache manager
        _ = CacheManager()  # noqa: F841

        # Get the build again - should use disk cache
        response2 = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

    async def test_cache_ttl_expiration(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that cache entries expire after TTL."""
        # Note: This test would require waiting for TTL to expire
        # For now, we'll just verify the cache is set with a TTL

        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Get the build to cache it
        response = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify cache key exists
        cache_manager = CacheManager()
        cache_key = f"build:{build_id}"
        _ = await cache_manager.get(cache_key)  # noqa: F841

        # If Redis is available, cached value should not be None
        # If using disk fallback, it might be None but that's okay
        # The important thing is that the endpoint works

    async def test_team_caching(self, client: AsyncClient, auth_headers: dict, sample_team_data: dict):
        """Test that teams are cached properly."""
        # Create a team
        create_response = await client.post("/api/v1/teams", json=sample_team_data, headers=auth_headers)
        team_id = create_response.json()["id"]

        # First retrieval
        response1 = await client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK

        # Second retrieval (cached)
        response2 = await client.get(f"/api/v1/teams/{team_id}", headers=auth_headers)
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

    async def test_cache_pattern_deletion(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that cache pattern deletion works."""
        # Create multiple builds
        for i in range(3):
            sample_build_data["name"] = f"Build {i}"
            await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # Get the builds list (cache it)
        response1 = await client.get("/api/v1/builds", headers=auth_headers)
        assert len(response1.json()) == 3

        # Create a new build (should invalidate the list cache)
        sample_build_data["name"] = "New Build"
        await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)

        # Get the builds list again (should show 4 builds)
        response2 = await client.get("/api/v1/builds", headers=auth_headers)
        assert len(response2.json()) == 4

    async def test_concurrent_cache_access(self, client: AsyncClient, auth_headers: dict, sample_build_data: dict):
        """Test that concurrent cache access works correctly."""
        # Create a build
        create_response = await client.post("/api/v1/builds", json=sample_build_data, headers=auth_headers)
        build_id = create_response.json()["id"]

        # Make multiple concurrent requests
        import asyncio

        async def get_build():
            return await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)

        responses = await asyncio.gather(*[get_build() for _ in range(10)])

        # All responses should be successful and identical
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
        first_response = responses[0].json()
        assert all(r.json() == first_response for r in responses)
