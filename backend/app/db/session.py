"""Database session management.

Ce module fournit la dépendance `get_db` utilisée par les endpoints FastAPI.
Il réutilise l'engine et la factory de sessions définis dans `app.db.base`,
qui s'appuient déjà sur `settings.DATABASE_URL` (donc sur le `.env`).
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import SessionLocal as AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
