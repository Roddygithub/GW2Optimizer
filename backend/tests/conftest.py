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
from app.db.models import UserDB as User  # Import your models here
from app.core.security import create_access_token, get_password_hash
import os

# Use TEST_DATABASE_URL from environment, fallback to SQLite in-memory
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# Main engine for unit/API tests
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

# SQLite engine for integration tests (better transaction isolation)
# Using SQLite ensures commits are immediately visible across sessions
INTEGRATION_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
integration_engine = create_async_engine(INTEGRATION_TEST_DATABASE_URL, echo=False)
IntegrationSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=integration_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test, with cleanup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Enable autocommit for integration tests to avoid foreign key issues
        yield session
        # Don't rollback - let the drop_all clean up

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def redis_client() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    """Yield a fake Redis client for tests."""
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.flushall()


@pytest_asyncio.fixture()
async def client(
    db_session: AsyncSession, redis_client: fakeredis.aioredis.FakeRedis
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTP client for the API, with overridden dependencies (unit/API tests)."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: redis_client

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def integration_client(
    redis_client: fakeredis.aioredis.FakeRedis,
) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTP client for integration tests with independent sessions per request.

    Uses SQLite instead of PostgreSQL to avoid transaction isolation issues.
    SQLite commits are immediately visible across all sessions.
    """

    # Create tables once using SQLite engine
    async with integration_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Each HTTP request gets its own session from SQLite
    async def get_test_db():
        async with IntegrationSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_redis_client] = lambda: redis_client

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

    # Clean up tables
    async with integration_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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
    # Force load all attributes to avoid lazy loading issues
    _ = user.id  # Access id to ensure it's loaded
    _ = user.email
    _ = user.username
    # Attach plain password for tests (not persisted)
    setattr(user, "password", user_data["password"])
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Return authentication headers for the test user."""
    access_token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_build_data():
    """Sample build data for testing."""
    return {
        "name": "Test Guardian Firebrand",
        "profession": "Guardian",
        "specialization": "Firebrand",
        "game_mode": "zerg",
        "role": "support",
        "description": "Test build for CI/CD validation",
        "trait_lines": [
            {"id": 1, "name": "Zeal", "traits": [1950, 1942, 1945]},
            {"id": 42, "name": "Radiance", "traits": [2101, 2159, 2154]},
            {"id": 62, "name": "Firebrand", "traits": [2075, 2103, 2083]},
        ],
        "skills": [
            {"slot": "heal", "id": 9153, "name": "Shelter"},
            {"slot": "utility1", "id": 9246, "name": "Mantra of Liberation"},
            {"slot": "utility2", "id": 9153, "name": "Mantra of Solace"},
            {"slot": "utility3", "id": 9175, "name": "Mantra of Lore"},
            {"slot": "elite", "id": 43123, "name": "Feel My Wrath"},
        ],
        "equipment": [],
        "synergies": ["might", "quickness", "stability"],
        "counters": [],
        "tags": ["wvw", "support", "firebrand"],
        "is_public": True,
    }


@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "name": "Test WvW Zerg Team",
        "game_mode": "zerg",
        "team_size": 50,
        "description": "Test team composition for WvW zerg",
        "is_public": True,
    }
