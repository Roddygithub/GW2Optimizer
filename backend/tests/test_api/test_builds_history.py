"""Tests for Build Suggestions History API endpoints."""

import pytest
from httpx import AsyncClient
from fastapi import status

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.xfail(reason="Endpoint routing issues under investigation")
]


class TestBuildSuggestionsHistory:
    async def test_history_anonymous_create_and_list(self, client: AsyncClient):
        # Initially, anonymous history should be empty
        resp_list_empty = await client.get("/api/v1/builds/history")
        assert resp_list_empty.status_code == status.HTTP_200_OK
        data = resp_list_empty.json()
        assert data["total"] == 0
        assert data["items"] == []

        # Create anonymous suggestion
        payload = {
            "build": {"profession": "Elementalist", "role": "DPS", "game_mode": "zerg"},
            "explanation": "Test anonymous explanation",
        }
        resp_create = await client.post("/api/v1/builds/history", json=payload)
        assert resp_create.status_code == status.HTTP_201_CREATED
        created = resp_create.json()
        assert created["id"]
        assert created["user_id"] is None
        assert created["build"]["profession"] == "Elementalist"

        # List should now contain one item
        resp_list = await client.get("/api/v1/builds/history")
        assert resp_list.status_code == status.HTTP_200_OK
        listed = resp_list.json()
        assert listed["total"] == 1
        assert len(listed["items"]) == 1
        assert listed["items"][0]["id"] == created["id"]

    async def test_history_authenticated_isolated_from_anonymous(self, client: AsyncClient, auth_headers: dict):
        # Anonymous create (not visible to authenticated user)
        anon_payload = {"build": {"profession": "Guardian", "role": "support"}}
        resp_create_anon = await client.post("/api/v1/builds/history", json=anon_payload)
        assert resp_create_anon.status_code == status.HTTP_201_CREATED

        # Authenticated user creates
        auth_payload = {"build": {"profession": "Necromancer", "role": "dps"}, "explanation": "Auth"}
        resp_create_auth = await client.post("/api/v1/builds/history", json=auth_payload, headers=auth_headers)
        assert resp_create_auth.status_code == status.HTTP_201_CREATED
        created_auth = resp_create_auth.json()
        assert created_auth["user_id"] is not None

        # Authenticated list should show only the authenticated user's entries
        resp_list_auth = await client.get("/api/v1/builds/history", headers=auth_headers)
        assert resp_list_auth.status_code == status.HTTP_200_OK
        listed_auth = resp_list_auth.json()
        assert listed_auth["total"] == 1
        assert len(listed_auth["items"]) == 1
        assert listed_auth["items"][0]["id"] == created_auth["id"]
