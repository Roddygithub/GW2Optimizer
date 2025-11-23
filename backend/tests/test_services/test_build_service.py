"""Tests for BuildService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.build import BuildCreate, BuildUpdate, GameMode, Profession
from app.models.user import UserDB
from app.services.build_service_db import BuildService


pytestmark = pytest.mark.asyncio


class TestBuildService:
    """Test suite for BuildService."""

    async def test_list_user_builds_empty(self, db_session: AsyncSession, test_user: UserDB) -> None:
        """list_user_builds should return an empty list when user has no builds."""
        service = BuildService(db_session)

        builds = await service.list_user_builds(test_user)

        assert builds == []

    async def test_create_build_success(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test successful build creation."""
        service = BuildService(db_session)
        build_data = BuildCreate(**sample_build_data)

        result = await service.create_build(build_data, test_user)

        assert result is not None
        assert result.name == sample_build_data["name"]
        assert result.profession == sample_build_data["profession"]
        assert str(result.user_id) == str(test_user.id)
        assert result.is_public == sample_build_data["is_public"]

    async def test_create_build_with_invalid_profession(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test build creation with invalid profession."""
        _ = BuildService(db_session)  # noqa: F841
        sample_build_data["profession"] = "InvalidProfession"

        with pytest.raises(ValueError):
            BuildCreate(**sample_build_data)

    async def test_get_build_by_owner(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test getting a build by its owner."""
        service = BuildService(db_session)
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        retrieved_build = await service.get_build(created_build.id, test_user)

        assert retrieved_build is not None
        assert retrieved_build.id == created_build.id
        assert retrieved_build.name == created_build.name
        assert str(retrieved_build.user_id) == str(test_user.id)

    async def test_get_public_build_by_other_user(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test getting a public build by another user."""
        service = BuildService(db_session)
        sample_build_data["is_public"] = True
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create another user
        other_user = UserDB(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        retrieved_build = await service.get_build(created_build.id, other_user)

        assert retrieved_build is not None
        assert retrieved_build.id == created_build.id

    async def test_get_private_build_by_other_user_fails(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test that private builds cannot be accessed by other users."""
        service = BuildService(db_session)
        sample_build_data["is_public"] = False
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create another user
        other_user = UserDB(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        with pytest.raises(HTTPException) as exc_info:
            await service.get_build(created_build.id, other_user)

        assert exc_info.value.status_code == 404

    async def test_get_nonexistent_build(self, db_session: AsyncSession, test_user: UserDB):
        """Test getting a build that doesn't exist."""
        service = BuildService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            await service.get_build("nonexistent-id", test_user)

        assert exc_info.value.status_code == 404

    async def test_list_user_builds(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test listing builds for a user."""
        service = BuildService(db_session)

        # Create multiple builds
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        sample_build_data["name"] = "Second Build"
        sample_build_data["profession"] = "Necromancer"
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        builds = await service.list_user_builds(test_user)

        assert len(builds) == 2
        assert all(str(build.user_id) == str(test_user.id) for build in builds)

    async def test_list_user_builds_with_profession_filter(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test listing builds with profession filter."""
        service = BuildService(db_session)

        # Create builds with different professions
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        sample_build_data["name"] = "Necro Build"
        sample_build_data["profession"] = "Necromancer"
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        guardian_builds = await service.list_user_builds(test_user, profession=Profession.GUARDIAN)

        assert len(guardian_builds) == 1
        assert guardian_builds[0].profession == "Guardian"

    async def test_list_user_builds_with_game_mode_filter(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test listing builds with game mode filter."""
        service = BuildService(db_session)

        # Create builds with different game modes
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        sample_build_data["name"] = "Roaming Build"
        sample_build_data["game_mode"] = "roaming"
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        zerg_builds = await service.list_user_builds(test_user, game_mode=GameMode.ZERG)

        assert len(zerg_builds) == 1
        assert zerg_builds[0].game_mode == "zerg"

    async def test_list_public_builds(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test listing public builds."""
        service = BuildService(db_session)

        # Create public build
        sample_build_data["is_public"] = True
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create private build
        sample_build_data["name"] = "Private Build"
        sample_build_data["is_public"] = False
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        public_builds = await service.list_public_builds()

        assert len(public_builds) == 1
        assert all(build.is_public for build in public_builds)

    async def test_update_build_success(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test successful build update."""
        service = BuildService(db_session)
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        update_data = BuildUpdate(
            name="Updated Build Name",
            description="Updated description",
            is_public=False,
        )

        updated_build = await service.update_build(created_build.id, update_data, test_user)

        assert updated_build.name == "Updated Build Name"
        assert updated_build.description == "Updated description"
        assert updated_build.is_public is False

    async def test_update_build_unauthorized(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test that users cannot update builds they don't own."""
        service = BuildService(db_session)
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create another user
        other_user = UserDB(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        update_data = BuildUpdate(name="Hacked Build")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_build(created_build.id, update_data, other_user)

        assert exc_info.value.status_code == 404

    async def test_delete_build_success(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test successful build deletion."""
        service = BuildService(db_session)
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        result = await service.delete_build(created_build.id, test_user)

        assert result is True

        # Verify build is deleted
        with pytest.raises(HTTPException):
            await service.get_build(created_build.id, test_user)

    async def test_delete_build_unauthorized(
        self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict
    ):
        """Test that users cannot delete builds they don't own."""
        service = BuildService(db_session)
        created_build = await service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create another user
        other_user = UserDB(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_build(created_build.id, other_user)

        assert exc_info.value.status_code == 404

    async def test_count_user_builds(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test counting user builds."""
        service = BuildService(db_session)

        # Create builds
        await service.create_build(BuildCreate(**sample_build_data), test_user)
        sample_build_data["name"] = "Second Build"
        await service.create_build(BuildCreate(**sample_build_data), test_user)

        count = await service.count_user_builds(test_user)

        assert count == 2

    async def test_pagination(self, db_session: AsyncSession, test_user: UserDB, sample_build_data: dict):
        """Test pagination of build listings."""
        service = BuildService(db_session)

        # Create 5 builds
        for i in range(5):
            sample_build_data["name"] = f"Build {i}"
            await service.create_build(BuildCreate(**sample_build_data), test_user)

        # Get first page
        page1 = await service.list_user_builds(test_user, skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await service.list_user_builds(test_user, skip=2, limit=2)
        assert len(page2) == 2

        # Verify different builds
        assert page1[0].id != page2[0].id
