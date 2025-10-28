"""Test database connection and table creation."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base_class import Base
from app.models.gw2.entities import *  # Import all GW2 models to ensure they're registered with SQLAlchemy


async def test_database_connection():
    """Test database connection and table creation."""
    print("Testing database connection...")
    
    # Create a synchronous engine for testing
    sync_url = str(settings.DATABASE_URL).replace("+aiosqlite", "")
    engine = create_engine(sync_url)
    
    try:
        # Test connection
        with engine.connect() as conn:
            print("✅ Successfully connected to the database")
            
            # Create tables
            print("Creating tables...")
            Base.metadata.create_all(engine)
            print("✅ Tables created successfully")
            
            # List all tables
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print("\nTables in the database:")
            for table in tables:
                print(f"- {table}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_database_connection())
