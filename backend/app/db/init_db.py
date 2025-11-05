"""Database initialization."""

from app.core.logging import logger
from app.db.base_class import Base


async def init_db() -> None:
    """
    Initialize database.
    Creates all tables if they don't exist.
    """
    try:
        # Import engine here to avoid circular imports
        from app.db.base import engine

        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise


async def drop_db() -> None:
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    try:
        # Import engine here to avoid circular imports
        from app.db.base import engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("⚠️  All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Error dropping database: {e}")
        raise
