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
from app.db.base_class import Base
from app.db.session import engine

# Import all models so they're registered with Base.metadata
from app.db import models  # noqa: F401


async def init_db():
    """Create all tables in the test database."""
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gw2optimizer_test.db")
    
    # Remove existing SQLite database if it exists
    if database_url.startswith("sqlite") and "/" in database_url:
        db_path = database_url.split("///")[-1]
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️  Removed existing database at {db_path}")

    print(f"🔧 Initializing test database: {database_url}")

    # Create all tables
    async with engine.begin() as conn:
        print("✨ Creating tables...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Verify the connection
    async with engine.connect() as conn:
        from sqlalchemy import text
        result = await conn.execute(text('SELECT 1'))
        print(f'✅ Database connection test: {result.scalar() == 1}')
    
    print("✅ Database initialized successfully")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
