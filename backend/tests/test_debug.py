"""Debug test to check database setup."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_class import Base
from app.models.user import UserDB
from app.core.security import get_password_hash


pytestmark = pytest.mark.asyncio


async def test_metadata():
    """Test that metadata contains tables."""
    import app.models.user  # noqa: F401
    import app.models.build  # noqa: F401
    import app.models.team  # noqa: F401

    print(f"\nBase.metadata.tables: {list(Base.metadata.tables.keys())}")
    assert len(Base.metadata.tables) > 0, "No tables in metadata!"


async def test_database_tables(db_session: AsyncSession):
    """Test that database tables are created."""
    # Check that we can query the database
    from sqlalchemy import text

    # Get table names
    result = await db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result]
    print(f"\nTables in database: {tables}")
    print(f"Base.metadata.tables: {list(Base.metadata.tables.keys())}")

    assert "users" in tables, f"users table not found. Available tables: {tables}"


async def test_create_user(db_session: AsyncSession):
    """Test creating a user."""
    user = UserDB(
        email="debug@example.com",
        username="debuguser",
        hashed_password=get_password_hash("password"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "debug@example.com"
