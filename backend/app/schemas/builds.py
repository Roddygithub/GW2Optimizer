"""Pydantic schemas for build suggestion history."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BuildSuggestionCreate(BaseModel):  # type: ignore[misc]
    """Payload for persisting a generated build suggestion."""

    build: Dict[str, Any] = Field(..., description="Build suggestion payload returned by the AI")
    explanation: Optional[str] = Field(None, description="Optional explanation provided by the AI")


class BuildSuggestionOut(BaseModel):  # type: ignore[misc]
    """Serialized build suggestion entry."""

    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    build: Dict[str, Any]
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedBuildSuggestions(BaseModel):  # type: ignore[misc]
    """Paginated list of build suggestions."""

    items: List[BuildSuggestionOut]
    total: int
    page: int
    limit: int
    has_next: bool
