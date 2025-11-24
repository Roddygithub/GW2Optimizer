"""Script to initialize SQLite database for testing."""

import asyncio
import os
from sqlalchemy import text

# Configuration for SQLite
DB_PATH = "./gw2optimizer_test.db"


async def init_db():
    # Remove existing database file if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️  Removed existing database at {DB_PATH}")

    # Import database components
    from app.db.base_class import Base
    from app.db.session import engine

    # Import all models to ensure they are registered with SQLAlchemy
    from app.db import models  # noqa: F401

    print("🔄 Creating SQLite database tables...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Verify the connection
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(f"✅ SQLite connection test: {result.scalar() == 1}")


if __name__ == "__main__":
    try:
        asyncio.run(init_db())
        print("✅ SQLite database initialized successfully")
    except Exception as e:
        print(f"❌ SQLite database initialization failed: {str(e)}")
        import traceback

        traceback.print_exc()
        exit(1)
