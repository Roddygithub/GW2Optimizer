"""Database base configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.logging import logger

# Database URL
DATABASE_URL = settings.DATABASE_URL

# Create async engine
if "postgresql" in DATABASE_URL:
    # PostgreSQL async - ensure asyncpg driver
    if "postgresql+asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
    )
elif "sqlite" in DATABASE_URL:
    # SQLite async - ensure aiosqlite driver
    if "sqlite+aiosqlite" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    raise ValueError(f"Unsupported database URL: {DATABASE_URL}")

# Create async session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Yields:
        AsyncSession: Database session
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
