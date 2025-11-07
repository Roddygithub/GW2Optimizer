"""Unit tests for AI feedback helpers."""

import json
from pathlib import Path

from app.api.ai_feedback import _persist_feedback_fallback


def test_persist_feedback_fallback_writes_file(tmp_path):
    """The fallback writer should create a JSON file with expected contents."""

    base_dir = tmp_path / "feedback"
    payload = {"target_id": "t-123", "rating": 7, "meta": {"foo": "bar"}}

    saved_path = _persist_feedback_fallback(str(base_dir), payload, "user-42")
    file_path = Path(saved_path)

    assert file_path.exists(), "Fallback writer must create a file"

    data = json.loads(file_path.read_text(encoding="utf-8"))
    assert data["user_id"] == "user-42"
    assert data["data"] == payload
    assert "ts" in data and data["ts"], "Timestamp should be recorded"
