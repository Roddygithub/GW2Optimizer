"""API tests for build endpoints.

These tests cover the main database-backed build routes exposed under /api/v1/builds.
They rely on the shared test fixtures (client, auth_headers, sample_build_data) and
must not perform any external HTTP calls.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_builds_empty(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/v1/builds should return 200 and an empty list when no builds exist."""
    response = await client.get("/api/v1/builds", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


@pytest.mark.asyncio
async def test_create_and_get_build(client: AsyncClient, auth_headers: dict, sample_build_data: dict) -> None:
    """Create a build via the API then retrieve it by ID and via the list endpoint."""
    # Create build
    create_resp = await client.post("/api/v1/builds", headers=auth_headers, json=sample_build_data)
    assert create_resp.status_code == 201

    created = create_resp.json()
    build_id = created["id"]

    # List builds
    list_resp = await client.get("/api/v1/builds", headers=auth_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert isinstance(items, list)
    assert any(item["id"] == build_id for item in items)

    # Get by ID
    get_resp = await client.get(f"/api/v1/builds/{build_id}", headers=auth_headers)
    assert get_resp.status_code == 200

    fetched = get_resp.json()
    assert fetched["id"] == build_id
    assert fetched["name"] == sample_build_data["name"]
    assert fetched["profession"] == sample_build_data["profession"]


@pytest.mark.asyncio
async def test_get_build_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """GET /api/v1/builds/{id} should return 404 for a non-existent build ID."""
    resp = await client.get("/api/v1/builds/nonexistent-id", headers=auth_headers)

    assert resp.status_code == 404
    body = resp.json()
    assert body.get("detail") == "Build not found"
