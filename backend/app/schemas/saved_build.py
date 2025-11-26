"""Pydantic schemas for saved builds."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class SavedBuildCreate(BaseModel):
    """Payload for creating a saved build entry.

    Typically created from an analysis result (manual Build Lab or URL-based
    analysis).
    """

    name: str = Field(..., max_length=200, description="Human-friendly name for the saved build")
    chat_code: Optional[str] = Field(
        None,
        description="GW2 build chat code if available (e.g. [&DQExOS47AAAA...=])",
        max_length=255,
    )
    profession: Optional[str] = Field(None, max_length=50, description="Profession name (e.g. Guardian)")
    specialization: Optional[str] = Field(None, max_length=100, description="Specialization name (e.g. Firebrand)")
    game_mode: Optional[str] = Field(None, max_length=50, description="Game mode or context (e.g. WvW Zerg)")
    synergy_score: Optional[str] = Field(
        None,
        max_length=8,
        description="Synergy score from the AI (e.g. S, A, B, C, or N/A)",
    )
    source_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Original source URL for this build when imported from an external site",
    )
    notes: Optional[str] = Field(None, description="Optional notes or AI summary for this build")


class SavedBuildOut(BaseModel):
    """Serialized saved build entry returned by the API."""

    id: int
    user_id: UUID
    name: str
    chat_code: Optional[str] = None
    profession: Optional[str] = None
    specialization: Optional[str] = None
    game_mode: Optional[str] = None
    synergy_score: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
