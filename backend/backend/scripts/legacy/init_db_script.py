import asyncio
from app.db.init_db import init_db, drop_db


async def main():
    # Drop all tables first (be careful in production!)
    try:
        print("Dropping all tables...")
        await drop_db()
        print("✅ All tables dropped")
    except Exception as e:
        print(f"⚠️  Error dropping tables: {e}")

    # Initialize database with all tables
    try:
        print("Initializing database...")
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
