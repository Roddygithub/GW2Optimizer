#!/usr/bin/env python3
"""
Initialize test database with all tables.
Used in CI to create tables before running tests.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base


async def init_db():
    """Create all tables in the test database."""
    database_url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/gw2optimizer_test")

    print(f"🔧 Initializing test database: {database_url}")

    engine = create_async_engine(database_url, echo=True)

    async with engine.begin() as conn:
        # Create tables if they don't exist (idempotent)
        print("✨ Creating tables (if not exist)...")
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ Test database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
