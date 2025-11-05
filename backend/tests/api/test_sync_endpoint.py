"""Test the sync endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import Settings, settings
from app.main import app, include_routers
from app.services.etl_gw2 import sync_all

# Ensure the API router is included
include_routers(app)

# Debug: Print all registered routes
print("\n=== Registered Routes ===")
for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", ["WebSocket"])
    name = getattr(route, "name", None)
    print(f"{path} - {methods} - {name}")
print("======================\n")

# Print the full path to the sync module for debugging
print(f"Sync module path: {os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app/api/sync.py'))}")
print(
    f"Sync module exists: {os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app/api/sync.py')))}"
)

# Print the content of the sync module for debugging
with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app/api/sync.py")), "r") as f:
    print("\n=== Sync Module Content ===")
    print(f.read())
    print("=========================\n")


@pytest.mark.asyncio
async def test_sync_gw2_endpoint_unauthorized(client: AsyncClient, monkeypatch) -> None:
    """Test that the sync endpoint requires authentication when GW2_SYNC_OPEN is False."""

    # Mock settings to include GW2_SYNC_OPEN
    mock_settings = Settings()
    mock_settings.GW2_SYNC_OPEN = False

    with patch("app.api.sync.settings", mock_settings):
        # Utiliser le chemin complet avec le préfixe API
        response = await client.post("/api/v1/sync/gw2")
        assert (
            response.status_code == status.HTTP_401_UNAUTHORIZED
        ), f"Expected 401, got {response.status_code}. Response: {response.text}"


@pytest.mark.asyncio
async def test_sync_gw2_endpoint_success(client: AsyncClient, monkeypatch) -> None:
    """Test successful sync endpoint call when GW2_SYNC_OPEN is True."""

    mock_result = {"items": {"inserted": 5, "updated": 2, "skipped": 0}}

    # Mock settings to include GW2_SYNC_OPEN
    mock_settings = Settings()
    mock_settings.GW2_SYNC_OPEN = True

    with patch("app.api.sync.settings", mock_settings):
        with patch("app.api.sync.sync_all", new_callable=AsyncMock, return_value=mock_result) as mock_sync:
            # Utiliser le chemin complet avec le préfixe API
            response = await client.post("/api/v1/sync/gw2")

            assert (
                response.status_code == status.HTTP_202_ACCEPTED
            ), f"Expected 202, got {response.status_code}. Response: {response.text}"
            assert response.json() == {"status": "accepted", "result": mock_result}
            mock_sync.assert_awaited_once()
