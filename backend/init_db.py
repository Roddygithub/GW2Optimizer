"""Script to initialize the database."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the database directory exists
os.makedirs("./data/local_db", exist_ok=True)


async def main():
    """Initialize the database."""
    from app.db.init_db import init_db, drop_db

    print("Initializing database...")
    try:
        # Drop all tables first (be careful in production!)
        print("Dropping existing tables...")
        await drop_db()
        print("✅ Tables dropped")

        # Initialize database with all tables
        await init_db()
        print("✅ Database initialized successfully")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
