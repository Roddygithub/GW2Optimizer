"""Debug script to test database initialization."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.db.base_class import Base
from app.db.init_db import init_db, drop_db
from app.db.base import engine
from app.models import __all__  # Import all models to register them with SQLAlchemy

async def debug_database():
    """Debug database initialization and table creation."""
    print("=== Starting database debug ===")
    
    # Print database URL
    print(f"Database URL: {engine.url}")
    
    # Check if models are registered
    print("\n=== Registered Tables ===")
    for table_name, table in Base.metadata.tables.items():
        print(f"- {table_name} ({', '.join(col.name for col in table.columns)})")
    
    # Try to drop and recreate tables
    print("\n=== Dropping all tables ===")
    try:
        await drop_db()
        print("✅ Tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
    
    print("\n=== Creating all tables ===")
    try:
        await init_db()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
    
    # Verify tables were created
    print("\n=== Verifying tables ===")
    async with engine.connect() as conn:
        from sqlalchemy import text
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        )
        tables = result.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
    
    print("\n=== Database debug complete ===")

if __name__ == "__main__":
    asyncio.run(debug_database())
