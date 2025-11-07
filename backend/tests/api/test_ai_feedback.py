"""API tests for the /api/v1/ai/feedback endpoint."""

from __future__ import annotations

import asyncio
from typing import Optional

import pytest
from httpx import AsyncClient

from app.api import ai_feedback as api_module
from app.main import app


@pytest.mark.asyncio
async def test_ai_feedback_endpoint_bg_trigger(monkeypatch, tmp_path):
    """Ensure feedback is recorded and trainer trigger is scheduled when enabled."""

    class DummySettings:
        ML_TRAINING_ENABLED = True
        LEARNING_DATA_DIR = str(tmp_path / "fb")

    dummy_settings = DummySettings()

    # Provide deterministic handler and trainer for the endpoint
    recorded: dict[str, Optional[dict]] = {"payload": None}

    class DummyHandler:
        def record_feedback(self, **kwargs):
            recorded["payload"] = kwargs
            return "fb-123"

    called = {"count": 0}

    def fake_trigger(settings):
        called["count"] += 1
        assert settings is dummy_settings

    app.dependency_overrides[api_module.get_settings] = lambda: dummy_settings
    monkeypatch.setattr(api_module, "get_feedback_handler", lambda: DummyHandler(), raising=False)
    monkeypatch.setattr(api_module, "trigger_incremental_training", fake_trigger, raising=False)

    # Avoid hitting the real auth/database dependencies during the request
    from app.core.security import get_current_user_optional

    app.dependency_overrides[get_current_user_optional] = lambda: None

    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ai/feedback",
                json={"target_id": "comp-42", "rating": 8, "comment": "Great"},
            )

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "accepted"
        assert body["training"] == "scheduled"
        assert recorded["payload"] is not None
        assert recorded["payload"]["composition_id"] == "comp-42"
        assert recorded["payload"]["rating"] == 8

        # Background tasks run after the response is returned; yield control to ensure completion
        await asyncio.sleep(0)
        assert called["count"] >= 1

    finally:
        app.dependency_overrides.pop(api_module.get_settings, None)
        app.dependency_overrides.pop(get_current_user_optional, None)
