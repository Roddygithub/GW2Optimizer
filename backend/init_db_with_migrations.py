"""Script to initialize the database and apply migrations."""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.base_class import Base
from app.db.init_db import drop_db, init_db


async def reset_database():
    """Drop and recreate the database."""
    print("Dropping existing database...")
    await drop_db()
    print("✅ Database dropped")

    print("Initializing database...")
    await init_db()
    print("✅ Database initialized")


def run_migrations():
    """Run Alembic migrations."""
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set the path to the alembic.ini file
    alembic_cfg = Config(os.path.join(current_dir, "alembic.ini"))
    
    # Set the script location to the alembic directory
    alembic_cfg.set_main_option("script_location", os.path.join(current_dir, "alembic"))
    
    # Set the SQLAlchemy URL
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
    
    print("Running migrations...")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations applied successfully")


async def main():
    """Main function to run the database initialization and migrations."""
    try:
        # Reset the database
        await reset_database()
        
        # Run migrations
        run_migrations()
        
        print("\n✅ Database setup completed successfully!")
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
