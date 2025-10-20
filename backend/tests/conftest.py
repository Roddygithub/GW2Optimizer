"""
Configuration and fixtures for pytest.

This file centralizes test setup, providing fixtures for database sessions,
HTTP clients, and authentication, ensuring tests are isolated and repeatable.
"""

import asyncio
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import fakeredis.aioredis

from app.main import app
from app.db.session import get_db
from app.core.redis import get_redis_client
from app.db.base import Base
from app.db.models import User  # Import your models here
from app.core.security import create_access_token, get_password_hash

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test, with rollback."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def redis_client() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    """Yield a fake Redis client for tests."""
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.flushall()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession, redis_client: fakeredis.aioredis.FakeRedis) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTP client for the API, with overridden dependencies."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: redis_client

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create and return a test user model instance."""
    user_data = {"email": "test@example.com", "username": "testuser", "password": "TestPassword123!"}
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password=get_password_hash(user_data["password"]),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    # Attach plain password for tests (not persisted)
    setattr(user, "password", user_data["password"])
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Return authentication headers for the test user."""
    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}