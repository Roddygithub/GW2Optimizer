"""
Initialize the test database with all tables.
This script is used in CI to create tables before running tests.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)

# Set environment variables for SQLite
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./gw2optimizer_test.db"
os.environ["REDIS_ENABLED"] = "false"

# Import SQLAlchemy and models after setting environment variables
from app.db.base_class import Base
from app.db.base import engine
from app.db import models  # noqa: F401


async def init_db():
    """Initialize the database by dropping and creating all tables."""
    print("🔧 Initializing test database...")
    async with engine.begin() as conn:
        print("🗑️  Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("✨ Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())
