"""Tests for TeamService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.team import TeamCompositionCreate, TeamCompositionUpdate
from app.models.build import BuildCreate
from app.models.user import UserDB
from app.services.team_service_db import TeamService
from app.services.build_service_db import BuildService


pytestmark = pytest.mark.asyncio


class TestTeamService:
    """Test suite for TeamService."""

    async def test_create_team_success(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test successful team creation."""
        service = TeamService(db_session)
        team_data = TeamCompositionCreate(**sample_team_data)

        result = await service.create_team(team_data, test_user)

        assert result is not None
        assert result.name == sample_team_data["name"]
        assert result.game_mode == sample_team_data["game_mode"]
        assert result.user_id == test_user.id
        assert result.is_public == sample_team_data["is_public"]

    async def test_create_team_with_builds(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict, sample_build_data: dict
    ):
        """Test creating a team with builds."""
        # Create builds first
        build_service = BuildService(db_session)
        build1 = await build_service.create_build(BuildCreate(**sample_build_data), test_user)

        sample_build_data["name"] = "Second Build"
        sample_build_data["profession"] = "Necromancer"
        build2 = await build_service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create team with builds
        team_service = TeamService(db_session)
        sample_team_data["build_ids"] = [build1.id, build2.id]
        team_data = TeamCompositionCreate(**sample_team_data)

        result = await team_service.create_team(team_data, test_user)

        assert result is not None
        assert len(result.slots) == 2

    async def test_get_team_by_owner(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test getting a team by its owner."""
        service = TeamService(db_session)
        created_team = await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        retrieved_team = await service.get_team(created_team.id, test_user)

        assert retrieved_team is not None
        assert retrieved_team.id == created_team.id
        assert retrieved_team.name == created_team.name
        assert retrieved_team.user_id == test_user.id

    async def test_get_public_team_by_other_user(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict
    ):
        """Test getting a public team by another user."""
        service = TeamService(db_session)
        sample_team_data["is_public"] = True
        created_team = await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

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

        retrieved_team = await service.get_team(created_team.id, other_user)

        assert retrieved_team is not None
        assert retrieved_team.id == created_team.id

    async def test_get_private_team_by_other_user_fails(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict
    ):
        """Test that private teams cannot be accessed by other users."""
        service = TeamService(db_session)
        sample_team_data["is_public"] = False
        created_team = await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

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
            await service.get_team(created_team.id, other_user)

        assert exc_info.value.status_code == 404

    async def test_list_user_teams(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test listing teams for a user."""
        service = TeamService(db_session)

        # Create multiple teams
        await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        sample_team_data["name"] = "Second Team"
        await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        teams = await service.list_user_teams(test_user)

        assert len(teams) == 2
        assert all(team.user_id == test_user.id for team in teams)

    async def test_list_public_teams(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test listing public teams."""
        service = TeamService(db_session)

        # Create public team
        sample_team_data["is_public"] = True
        await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        # Create private team
        sample_team_data["name"] = "Private Team"
        sample_team_data["is_public"] = False
        await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        public_teams = await service.list_public_teams()

        assert len(public_teams) == 1
        assert all(team.is_public for team in public_teams)

    async def test_update_team_success(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test successful team update."""
        service = TeamService(db_session)
        created_team = await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        update_data = TeamCompositionUpdate(
            name="Updated Team Name",
            description="Updated description",
            is_public=False,
        )

        updated_team = await service.update_team(created_team.id, update_data, test_user)

        assert updated_team.name == "Updated Team Name"
        assert updated_team.description == "Updated description"
        assert updated_team.is_public is False

    async def test_update_team_unauthorized(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test that users cannot update teams they don't own."""
        service = TeamService(db_session)
        created_team = await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

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

        update_data = TeamCompositionUpdate(name="Hacked Team")

        with pytest.raises(HTTPException) as exc_info:
            await service.update_team(created_team.id, update_data, other_user)

        assert exc_info.value.status_code == 404

    async def test_delete_team_success(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test successful team deletion."""
        service = TeamService(db_session)
        created_team = await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        result = await service.delete_team(created_team.id, test_user)

        assert result is True

        # Verify team is deleted
        with pytest.raises(HTTPException):
            await service.get_team(created_team.id, test_user)

    async def test_add_build_to_team(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict, sample_build_data: dict
    ):
        """Test adding a build to a team."""
        # Create a build
        build_service = BuildService(db_session)
        build = await build_service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create a team
        team_service = TeamService(db_session)
        team = await team_service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        # Add build to team
        updated_team = await team_service.add_build_to_team(team.id, build.id, test_user)

        assert len(updated_team.slots) == 1
        assert updated_team.slots[0].build_id == build.id

    async def test_add_public_build_to_team(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict, sample_build_data: dict
    ):
        """Test adding a public build from another user to a team."""
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

        # Create a public build by other user
        build_service = BuildService(db_session)
        sample_build_data["is_public"] = True
        build = await build_service.create_build(BuildCreate(**sample_build_data), other_user)

        # Create a team by test_user
        team_service = TeamService(db_session)
        team = await team_service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        # Add other user's public build to team
        updated_team = await team_service.add_build_to_team(team.id, build.id, test_user)

        assert len(updated_team.slots) == 1
        assert updated_team.slots[0].build_id == build.id

    async def test_add_private_build_to_team_fails(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict, sample_build_data: dict
    ):
        """Test that adding a private build from another user fails."""
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

        # Create a private build by other user
        build_service = BuildService(db_session)
        sample_build_data["is_public"] = False
        build = await build_service.create_build(BuildCreate(**sample_build_data), other_user)

        # Create a team by test_user
        team_service = TeamService(db_session)
        team = await team_service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        # Try to add other user's private build to team
        with pytest.raises(HTTPException) as exc_info:
            await team_service.add_build_to_team(team.id, build.id, test_user)

        assert exc_info.value.status_code == 404

    async def test_remove_build_from_team(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict, sample_build_data: dict
    ):
        """Test removing a build from a team."""
        # Create a build
        build_service = BuildService(db_session)
        build = await build_service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create a team with the build
        team_service = TeamService(db_session)
        team = await team_service.create_team(TeamCompositionCreate(**sample_team_data), test_user)
        team = await team_service.add_build_to_team(team.id, build.id, test_user)

        slot_id = team.slots[0].id

        # Remove build from team
        updated_team = await team_service.remove_build_from_team(team.id, slot_id, test_user)

        assert len(updated_team.slots) == 0

    async def test_slot_number_auto_increment(
        self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict, sample_build_data: dict
    ):
        """Test that slot numbers are auto-incremented."""
        # Create builds
        build_service = BuildService(db_session)
        build1 = await build_service.create_build(BuildCreate(**sample_build_data), test_user)

        sample_build_data["name"] = "Second Build"
        build2 = await build_service.create_build(BuildCreate(**sample_build_data), test_user)

        # Create team and add builds
        team_service = TeamService(db_session)
        team = await team_service.create_team(TeamCompositionCreate(**sample_team_data), test_user)
        team = await team_service.add_build_to_team(team.id, build1.id, test_user)
        team = await team_service.add_build_to_team(team.id, build2.id, test_user)

        assert team.slots[0].slot_number == 1
        assert team.slots[1].slot_number == 2

    async def test_count_user_teams(self, db_session: AsyncSession, test_user: UserDB, sample_team_data: dict):
        """Test counting user teams."""
        service = TeamService(db_session)

        # Create teams
        await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)
        sample_team_data["name"] = "Second Team"
        await service.create_team(TeamCompositionCreate(**sample_team_data), test_user)

        count = await service.count_user_teams(test_user)

        assert count == 2
