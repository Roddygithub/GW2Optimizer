"""Tests for BuildService with database persistence."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from app.models.build import BuildCreate, BuildDB, BuildUpdate, GameMode, Profession, Role
from app.models.user import UserDB
from app.services.build_service_db import BuildService


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = UserDB(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def build_data():
    """Sample build creation data."""
    return BuildCreate(
        name="Test Firebrand",
        profession=Profession.GUARDIAN,
        specialization="Firebrand",
        game_mode=GameMode.ZERG,
        role=Role.SUPPORT,
        description="Test build",
        is_public=True,
        trait_lines=[],
        skills=[],
        equipment=[],
        synergies=["Might", "Quickness"],
        counters=["Necromancer"]
    )


@pytest.mark.asyncio
async def test_create_build_success(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test successful build creation."""
    service = BuildService(db_session)
    
    build = await service.create_build(build_data, test_user)
    
    assert build is not None
    assert build.name == "Test Firebrand"
    assert build.profession == "Guardian"
    assert build.user_id == test_user.id
    assert build.is_public is True


@pytest.mark.asyncio
async def test_get_build_owner(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test getting a build by its owner."""
    service = BuildService(db_session)
    
    # Create build
    created_build = await service.create_build(build_data, test_user)
    
    # Get build
    retrieved_build = await service.get_build(created_build.id, test_user)
    
    assert retrieved_build is not None
    assert retrieved_build.id == created_build.id
    assert retrieved_build.name == created_build.name


@pytest.mark.asyncio
async def test_get_build_public(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test getting a public build by another user."""
    service = BuildService(db_session)
    
    # Create public build
    created_build = await service.create_build(build_data, test_user)
    
    # Create another user
    other_user = UserDB(
        id="other-user-id",
        email="other@example.com",
        username="otheruser",
        hashed_password="hashed_password"
    )
    db_session.add(other_user)
    await db_session.commit()
    
    # Get build as other user (should work because it's public)
    retrieved_build = await service.get_build(created_build.id, other_user)
    
    assert retrieved_build is not None
    assert retrieved_build.id == created_build.id


@pytest.mark.asyncio
async def test_get_build_private_unauthorized(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test that private builds cannot be accessed by other users."""
    service = BuildService(db_session)
    
    # Create private build
    build_data.is_public = False
    created_build = await service.create_build(build_data, test_user)
    
    # Create another user
    other_user = UserDB(
        id="other-user-id",
        email="other@example.com",
        username="otheruser",
        hashed_password="hashed_password"
    )
    db_session.add(other_user)
    await db_session.commit()
    
    # Try to get build as other user (should fail)
    retrieved_build = await service.get_build(created_build.id, other_user)
    
    assert retrieved_build is None


@pytest.mark.asyncio
async def test_list_user_builds(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test listing builds for a user."""
    service = BuildService(db_session)
    
    # Create multiple builds
    await service.create_build(build_data, test_user)
    
    build_data.name = "Second Build"
    build_data.profession = Profession.NECROMANCER
    await service.create_build(build_data, test_user)
    
    # List builds
    builds = await service.list_user_builds(test_user)
    
    assert len(builds) == 2


@pytest.mark.asyncio
async def test_list_builds_with_filters(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test listing builds with filters."""
    service = BuildService(db_service)
    
    # Create builds with different professions
    await service.create_build(build_data, test_user)
    
    build_data.name = "Necro Build"
    build_data.profession = Profession.NECROMANCER
    await service.create_build(build_data, test_user)
    
    # Filter by profession
    guardian_builds = await service.list_user_builds(
        test_user,
        profession=Profession.GUARDIAN
    )
    
    assert len(guardian_builds) == 1
    assert guardian_builds[0].profession == "Guardian"


@pytest.mark.asyncio
async def test_update_build(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test updating a build."""
    service = BuildService(db_session)
    
    # Create build
    created_build = await service.create_build(build_data, test_user)
    
    # Update build
    update_data = BuildUpdate(
        name="Updated Name",
        description="Updated description"
    )
    updated_build = await service.update_build(created_build.id, update_data, test_user)
    
    assert updated_build is not None
    assert updated_build.name == "Updated Name"
    assert updated_build.description == "Updated description"


@pytest.mark.asyncio
async def test_delete_build(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test deleting a build."""
    service = BuildService(db_session)
    
    # Create build
    created_build = await service.create_build(build_data, test_user)
    build_id = created_build.id
    
    # Delete build
    result = await service.delete_build(build_id, test_user)
    
    assert result is True
    
    # Verify build is deleted
    deleted_build = await service.get_build(build_id, test_user)
    assert deleted_build is None


@pytest.mark.asyncio
async def test_count_user_builds(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test counting user builds."""
    service = BuildService(db_session)
    
    # Create builds
    await service.create_build(build_data, test_user)
    build_data.name = "Second Build"
    await service.create_build(build_data, test_user)
    
    # Count builds
    count = await service.count_user_builds(test_user)
    
    assert count == 2


@pytest.mark.asyncio
async def test_list_public_builds(db_session: AsyncSession, test_user: UserDB, build_data: BuildCreate):
    """Test listing public builds."""
    service = BuildService(db_session)
    
    # Create public build
    build_data.is_public = True
    await service.create_build(build_data, test_user)
    
    # Create private build
    build_data.name = "Private Build"
    build_data.is_public = False
    await service.create_build(build_data, test_user)
    
    # List public builds
    public_builds = await service.list_public_builds()
    
    assert len(public_builds) == 1
    assert public_builds[0].is_public is True
