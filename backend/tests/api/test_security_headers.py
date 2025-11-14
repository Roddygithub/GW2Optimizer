"""Tests for security-related headers."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_server_header_absent() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    header_keys = {key.lower() for key in response.headers.keys()}
    assert "server" not in header_keys
    assert "x-powered-by" not in header_keys
