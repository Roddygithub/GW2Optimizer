"""Saved builds API endpoints with database persistence."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user as get_current_user
from app.core.logging import logger
from app.db.base import get_db
from app.db.models import UserDB
from app.schemas.saved_build import SavedBuildCreate, SavedBuildOut
from app.services.saved_build_service import SavedBuildService


router = APIRouter()


@router.post("", response_model=SavedBuildOut, status_code=status.HTTP_201_CREATED)
async def create_saved_build(
    payload: SavedBuildCreate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedBuildOut:
    """Create a new saved build for the authenticated user.

    Typically called after an AI analysis (Build Lab or URL analysis) to
    persist the key metadata and AI evaluation.
    """

    service = SavedBuildService(db)
    saved = await service.create_saved_build(payload, current_user)

    logger.info(
        "Saved build created via API",
        extra={"saved_build_id": saved.id, "user_id": str(current_user.id)},
    )

    return SavedBuildOut.model_validate(saved)


@router.get("", response_model=List[SavedBuildOut])
async def list_saved_builds(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SavedBuildOut]:
    """List saved builds for the authenticated user."""

    service = SavedBuildService(db)
    items = await service.list_saved_builds(current_user)
    return [SavedBuildOut.model_validate(item) for item in items]


@router.delete("/{saved_build_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_build(
    saved_build_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a saved build belonging to the authenticated user."""

    service = SavedBuildService(db)
    await service.delete_saved_build(saved_build_id, current_user)

    logger.info(
        "Saved build deleted via API",
        extra={"saved_build_id": saved_build_id, "user_id": str(current_user.id)},
    )
