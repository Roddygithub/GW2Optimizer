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
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
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

# SQLite engine for integration tests will be created per fixture
# This ensures complete isolation between tests
IntegrationSessionLocal = None  # Will be set per test fixture


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test (unit/API tests).

    Simple session for fast unit and API tests.
    Creates/drops tables per test for isolation.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

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

    Uses PostgreSQL in CI (with data cleanup) or SQLite locally for complete isolation.
    """
    import tempfile
    import uuid

    # Determine database type from environment
    test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    is_postgresql = "postgresql" in test_db_url

    if is_postgresql:
        # Use PostgreSQL (CI environment) - simplified approach
        test_engine = engine  # Use global engine

        # Create tables if they don't exist
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Each HTTP request gets its own session
        async def get_test_db():
            async with TestSessionLocal() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db] = get_test_db
        app.dependency_overrides[get_redis_client] = lambda: redis_client

        async with AsyncClient(app=app, base_url="http://test") as c:
            yield c

        app.dependency_overrides.clear()

        # Clean up data after test using DELETE (safer than TRUNCATE)
        async with test_engine.begin() as conn:
            # Delete in correct order (respect foreign keys)
            await conn.execute(text("DELETE FROM team_slots"))
            await conn.execute(text("DELETE FROM team_compositions"))
            await conn.execute(text("DELETE FROM builds"))
            await conn.execute(text("DELETE FROM users"))
    else:
        # Use SQLite (local development)
        test_id = str(uuid.uuid4())[:8]
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{test_id}.db")
        db_path = db_file.name
        db_file.close()

        test_db_url = f"sqlite+aiosqlite:///{db_path}"
        test_engine = create_async_engine(
            test_db_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Enable foreign keys for SQLite
        @event.listens_for(test_engine.sync_engine, "connect")
        def enable_fk(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        TestSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create tables for SQLite
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Each HTTP request gets its own session
        async def get_test_db():
            async with TestSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db] = get_test_db
        app.dependency_overrides[get_redis_client] = lambda: redis_client

        async with AsyncClient(app=app, base_url="http://test") as c:
            yield c

        app.dependency_overrides.clear()

        # Clean up SQLite
        await test_engine.dispose()
        try:
            os.unlink(db_path)
        except Exception:
            pass


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
