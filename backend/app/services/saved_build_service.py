"""Service layer for managing saved builds."""

from __future__ import annotations

from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models import UserDB
from app.models.saved_build import SavedBuildDB
from app.schemas.saved_build import SavedBuildCreate


class SavedBuildService:
    """Service for CRUD operations on SavedBuildDB entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_saved_build(self, payload: SavedBuildCreate, user: UserDB) -> SavedBuildDB:
        """Create a new saved build for the given user."""

        raw_game_mode = payload.game_mode or None
        safe_game_mode = raw_game_mode[:50] if raw_game_mode is not None else None

        saved = SavedBuildDB(
            user_id=user.id,
            name=payload.name,
            chat_code=payload.chat_code,
            profession=payload.profession,
            specialization=payload.specialization,
            game_mode=safe_game_mode,
            synergy_score=payload.synergy_score,
            source_url=payload.source_url,
            notes=payload.notes,
        )

        self.db.add(saved)
        await self.db.commit()
        await self.db.refresh(saved)

        logger.info(
            "Saved build created",
            extra={"saved_build_id": saved.id, "user_id": str(user.id), "name": saved.name},
        )

        return saved

    async def list_saved_builds(self, user: UserDB) -> List[SavedBuildDB]:
        """List all saved builds for the given user, newest first."""

        stmt = (
            select(SavedBuildDB)
            .where(SavedBuildDB.user_id == user.id)
            .order_by(SavedBuildDB.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_saved_build(self, saved_build_id: int, user: UserDB) -> None:
        """Delete a saved build owned by the given user.

        Raises 404 if not found or not owned by the user.
        """

        stmt = select(SavedBuildDB).where(
            SavedBuildDB.id == saved_build_id,
            SavedBuildDB.user_id == user.id,
        )
        result = await self.db.execute(stmt)
        saved = result.scalar_one_or_none()

        if not saved:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved build not found")

        await self.db.delete(saved)
        await self.db.commit()

        logger.info(
            "Saved build deleted",
            extra={"saved_build_id": saved_build_id, "user_id": str(user.id)},
        )
