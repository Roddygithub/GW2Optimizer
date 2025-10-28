"""Database session management."""

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.logging import logger
from app.core.config import settings


def _build_database_url() -> str:
    """Construct the database URL with sensible fallbacks for non-Postgres environments."""

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            logger.warning("DATABASE_URL uses deprecated postgres:// prefix; updating to postgresql+asyncpg://")
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if not database_url.startswith("postgresql+"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url

    required_vars = {"POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_DB"}
    missing = sorted(var for var in required_vars if not os.getenv(var))

    if missing:
        if getattr(settings, "REQUIRE_POSTGRES", False):
            raise RuntimeError("Missing required Postgres environment variables: " + ", ".join(missing))

        logger.warning(
            "Postgres environment variables missing (%s); falling back to SQLite for documentation/test builds.",
            ", ".join(missing),
        )
        sqlite_path = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        return sqlite_path

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


DATABASE_URL = _build_database_url()

# Configure engine based on database type
if DATABASE_URL.startswith('sqlite'):
    # SQLite configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_size=getattr(settings, 'POOL_SIZE', 5),  # Default to 5 if not set
        max_overflow=getattr(settings, 'MAX_OVERFLOW', 10),  # Default to 10 if not set
    )

# Create async session factory
async_session = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
