"""AI feedback orchestration endpoint.

This module exposes the lightweight orchestrator for ingesting AI feedback and
triggering the incremental trainer behind a feature flag. It preserves the
existing feedback pipeline (JSON-per-feedback files managed by
``FeedbackHandler``) and only adds orchestration, background triggering, and
soft metrics hooks.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.ai.feedback import FeedbackType, get_feedback_handler
from app.ai.trainer import trigger_incremental_training
from app.core.config import Settings, settings
from app.core.logging import logger
from app.core.security import get_current_user_optional
from app.db.models import UserDB as User
from app.metrics_ai import feedback_total, training_triggers_total

router = APIRouter(tags=["AI Feedback"])


class FeedbackIn(BaseModel):
    """Payload submitted by clients when providing feedback."""

    target_id: str = Field(..., description="Target identifier (composition id)")
    rating: int = Field(..., ge=1, le=10, description="Explicit rating (1-10)")
    comment: Optional[str] = Field(None, description="Optional free-form comment")
    meta: Optional[Dict[str, Any]] = Field(None, description="Optional metadata payload")


def get_settings() -> Settings:
    """Return application settings (dependency override friendly)."""

    return settings


def _persist_feedback_fallback(base_dir: str, payload: Dict[str, Any], user_id: Optional[str]) -> str:
    """Persist feedback to a dedicated JSON file as a safety fallback."""

    directory = Path(base_dir)
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fallback_file = directory / f"feedback_{timestamp}_{uuid.uuid4().hex}.json"

    record = {
        "ts": timestamp,
        "user_id": user_id,
        "data": payload,
    }

    with fallback_file.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)

    return str(fallback_file)


@router.post("/feedback", status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(
    feedback_in: FeedbackIn,
    background_tasks: BackgroundTasks,
    cfg: Settings = Depends(get_settings),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Record feedback and trigger background incremental training when enabled."""

    user_id = str(current_user.id) if current_user else "anonymous"
    storage_label = "ok"
    feedback_id: Optional[str] = None

    handler_metadata = dict(feedback_in.meta or {})
    if feedback_in.comment:
        handler_metadata.setdefault("comment", feedback_in.comment)

    try:
        handler = get_feedback_handler()
        feedback_id = handler.record_feedback(  # type: ignore[arg-type]
            composition_id=feedback_in.target_id,
            user_id=user_id,
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=feedback_in.rating,
            comments=feedback_in.comment,
            metadata=handler_metadata,
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "Feedback handler failed; falling back to file storage",
            extra={"error": str(exc)},
        )
        storage_label = "fallback"
        try:
            payload = feedback_in.model_dump()
            payload["user_id"] = user_id
            payload["meta"] = handler_metadata
            feedback_id = _persist_feedback_fallback(cfg.LEARNING_DATA_DIR, payload, user_id)
        except Exception as fallback_exc:  # pragma: no cover - filesystem edge case
            logger.error(
                "Feedback persistence failed",
                extra={"error": str(fallback_exc)},
            )
            if feedback_total:
                feedback_total.labels(result="error").inc()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to record feedback")

    if feedback_total:
        feedback_total.labels(result=storage_label).inc()

    training_label = "disabled"
    try:
        if bool(getattr(cfg, "ML_TRAINING_ENABLED", False)):
            background_tasks.add_task(trigger_incremental_training, cfg)
            training_label = "scheduled"
        else:
            training_label = "disabled"
    except Exception as exc:  # pragma: no cover - scheduling guard
        logger.warning("Failed to schedule incremental training", extra={"error": str(exc)})
        training_label = "error"

    if training_triggers_total:
        training_triggers_total.labels(result=training_label).inc()

    logger.info(
        "AI feedback processed",
        extra={
            "target_id": feedback_in.target_id,
            "user_id": user_id,
            "storage": storage_label,
            "training": training_label,
        },
    )

    return {
        "status": "accepted",
        "feedback_id": feedback_id,
        "storage": storage_label,
        "training": training_label,
    }
