#!/usr/bin/env python3
"""
Initialize test database with all tables.
Used in CI to create tables before running tests.
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("db_init")

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)
logger.info(f"Added {backend_path} to Python path")

# Set environment variables for SQLite
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./gw2optimizer_test.db"
os.environ["REDIS_ENABLED"] = "false"

# Import SQLAlchemy and models after setting environment variables
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    # Import models to ensure they are registered with SQLAlchemy
    from app.db.base_class import Base
    from app.db import models  # noqa: F401

    logger.info("✅ Successfully imported SQLAlchemy and models")
except ImportError as e:
    logger.error(f"❌ Error importing modules: {e}", exc_info=True)
    logger.error(f"Current Python path: {sys.path}")
    sys.exit(1)


async def init_db():
    """Create all tables in the test database."""
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gw2optimizer_test.db")
    logger.info(f"🔧 Using database URL: {database_url}")

    # Configure engine with explicit SQLite settings
    engine = create_async_engine(
        database_url,
        echo=True,
        future=True,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    )

    # Create async session maker
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Remove existing SQLite database if it exists
    if database_url.startswith("sqlite") and "///" in database_url:
        db_path = database_url.split("///")[-1]
        if os.path.exists(db_path):
            logger.warning(f"🗑️  Removing existing database at {db_path}")
            try:
                os.remove(db_path)
                logger.info(f"✅ Successfully removed existing database at {db_path}")
            except Exception as e:
                logger.error(f"❌ Failed to remove database file: {e}")
                return False

    try:
        # Create all tables
        logger.info("🔄 Creating database tables...")
        async with engine.begin() as conn:
            logger.info("🗑️  Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("✨ Creating new tables...")
            await conn.run_sync(Base.metadata.create_all)

        # Verify the connection and table creation
        async with async_session() as session:
            logger.info("🔍 Verifying database connection...")
            result = await session.execute(text("SELECT 1"))
            test_result = result.scalar() == 1
            logger.info(f"✅ Database connection test: {test_result}")

            # Count the number of tables created
            result = await session.execute(
                text(
                    """
                    SELECT count(name) FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%';
                """
                )
            )
            table_count = result.scalar()
            logger.info(f"📊 Found {table_count} tables in the database")

        logger.info("✅ Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logger.info("🚀 Starting database initialization...")
    try:
        success = asyncio.run(init_db())
        if success:
            logger.info("✨ Database initialization completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Database initialization failed")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"💥 Fatal error during database initialization: {e}", exc_info=True)
        sys.exit(1)
