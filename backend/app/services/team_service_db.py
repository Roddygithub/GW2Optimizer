"""Team service with database persistence for GW2Optimizer."""

from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.build import BuildDB, GameMode
from app.models.team import TeamComposition, TeamCompositionCreate, TeamCompositionDB, TeamCompositionUpdate, TeamSlotDB
from app.db.models import UserDB


class TeamService:
    """Service for managing team compositions with database persistence."""

    def __init__(self, db: AsyncSession):
        """
        Initialize team service.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_team(self, team_data: TeamCompositionCreate, user: UserDB) -> TeamCompositionDB:
        """
        Create a new team composition for the user.

        Args:
            team_data: Team creation data
            user: User creating the team

        Returns:
            Created team from database

        Raises:
            HTTPException: If team creation fails or builds not found
        """
        try:
            # Validate that all build IDs exist and belong to user or are public
            if team_data.build_ids:
                for build_id in team_data.build_ids:
                    stmt = select(BuildDB).where(
                        and_(BuildDB.id == build_id, or_(BuildDB.user_id == str(user.id), BuildDB.is_public == True))
                    )
                    result = await self.db.execute(stmt)
                    build = result.scalar_one_or_none()
                    if not build:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Build {build_id} not found or not accessible",
                        )

            # Create team composition
            team_dict = team_data.model_dump(exclude={"build_ids"})
            team_db = TeamCompositionDB(id=str(uuid4()), user_id=str(user.id), **team_dict)

            self.db.add(team_db)

            # Create team slots for each build
            for idx, build_id in enumerate(team_data.build_ids, start=1):
                slot = TeamSlotDB(
                    id=str(uuid4()), team_composition_id=team_db.id, build_id=build_id, slot_number=idx, priority=1
                )
                self.db.add(slot)

            await self.db.commit()
            await self.db.refresh(team_db)

            logger.info(f"✅ Created team {team_db.id} for user {user.id}")
            return team_db

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error creating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create team: {str(e)}"
            )

    async def get_team(self, team_id: str, user: UserDB) -> Optional[TeamCompositionDB]:
        """
        Get a team by ID if it belongs to the user or is public.

        Args:
            team_id: Team ID
            user: Current user

        Returns:
            Team if found and accessible, None otherwise
        """
        try:
            stmt = (
                select(TeamCompositionDB)
                .options(selectinload(TeamCompositionDB.team_slots))
                .where(
                    and_(
                        TeamCompositionDB.id == team_id,
                        or_(TeamCompositionDB.user_id == str(user.id), TeamCompositionDB.is_public == True),
                    )
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"❌ Error getting team {team_id}: {e}")
            return None

    async def list_user_teams(
        self,
        user: UserDB,
        skip: int = 0,
        limit: int = 100,
        game_mode: Optional[GameMode] = None,
        is_public: Optional[bool] = None,
    ) -> List[TeamCompositionDB]:
        """
        List teams for a user with optional filters.

        Args:
            user: User whose teams to list
            skip: Number of records to skip
            limit: Maximum number of records to return
            game_mode: Filter by game mode
            is_public: Filter by public status

        Returns:
            List of teams
        """
        try:
            stmt = (
                select(TeamCompositionDB)
                .options(selectinload(TeamCompositionDB.team_slots))
                .where(TeamCompositionDB.user_id == str(user.id))
            )

            # Apply filters
            if game_mode:
                stmt = stmt.where(TeamCompositionDB.game_mode == game_mode.value)
            if is_public is not None:
                stmt = stmt.where(TeamCompositionDB.is_public == is_public)

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit).order_by(TeamCompositionDB.created_at.desc())

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Error listing teams for user {user.username}: {e}")
            return []

    async def list_public_teams(
        self, skip: int = 0, limit: int = 100, game_mode: Optional[GameMode] = None
    ) -> List[TeamCompositionDB]:
        """
        List public teams with optional filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            game_mode: Filter by game mode

        Returns:
            List of public teams
        """
        try:
            stmt = (
                select(TeamCompositionDB)
                .options(selectinload(TeamCompositionDB.team_slots))
                .where(TeamCompositionDB.is_public == True)
            )

            # Apply filters
            if game_mode:
                stmt = stmt.where(TeamCompositionDB.game_mode == game_mode.value)

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit).order_by(TeamCompositionDB.created_at.desc())

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Error listing public teams: {e}")
            return []

    async def update_team(
        self, team_id: str, team_data: TeamCompositionUpdate, user: UserDB
    ) -> Optional[TeamCompositionDB]:
        """
        Update a team if it belongs to the user.

        Args:
            team_id: Team ID to update
            team_data: Updated team data
            user: Current user

        Returns:
            Updated team if successful, None otherwise

        Raises:
            HTTPException: If team not found or user doesn't have permission
        """
        try:
            # Get the team
            team = await self.get_team(team_id, user)
            if not team:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

            # Check ownership
            if team.user_id != str(user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this team")

            # Update fields
            update_data = team_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(team, field, value)

            await self.db.commit()
            await self.db.refresh(team)

            logger.info(f"✅ Updated team {team_id} for user {user.id}")
            return team

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error updating team {team_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update team: {str(e)}"
            )

    async def delete_team(self, team_id: str, user: UserDB) -> bool:
        """
        Delete a team if it belongs to the user.

        Args:
            team_id: Team ID to delete
            user: Current user

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If team not found or user doesn't have permission
        """
        try:
            # Get the team
            team = await self.get_team(team_id, user)
            if not team:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

            # Check ownership
            if team.user_id != str(user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this team")

            # Delete the team (cascade will handle team_slots)
            await self.db.delete(team)
            await self.db.commit()

            logger.info(f"✅ Deleted team {team_id} for user {user.id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error deleting team {team_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete team: {str(e)}"
            )

    async def add_build_to_team(
        self,
        team_id: str,
        build_id: str,
        user: UserDB,
        slot_number: Optional[int] = None,
        player_name: Optional[str] = None,
    ) -> TeamSlotDB:
        """
        Add a build to a team composition.

        Args:
            team_id: Team ID
            build_id: Build ID to add
            user: Current user
            slot_number: Optional slot number (auto-assigned if not provided)
            player_name: Optional player name for the slot

        Returns:
            Created team slot

        Raises:
            HTTPException: If team or build not found, or user doesn't have permission
        """
        try:
            # Get the team
            team = await self.get_team(team_id, user)
            if not team:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

            # Check ownership
            if team.user_id != str(user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this team")

            # Validate build exists and is accessible
            stmt = select(BuildDB).where(
                and_(BuildDB.id == build_id, or_(BuildDB.user_id == str(user.id), BuildDB.is_public == True))
            )
            result = await self.db.execute(stmt)
            build = result.scalar_one_or_none()
            if not build:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found or not accessible")

            # Auto-assign slot number if not provided
            if slot_number is None:
                stmt = select(func.max(TeamSlotDB.slot_number)).where(TeamSlotDB.team_composition_id == team_id)
                result = await self.db.execute(stmt)
                max_slot = result.scalar_one_or_none()
                slot_number = (max_slot or 0) + 1

            # Create team slot
            slot = TeamSlotDB(
                id=str(uuid4()),
                team_composition_id=team_id,
                build_id=build_id,
                slot_number=slot_number,
                player_name=player_name,
                priority=1,
            )

            self.db.add(slot)
            await self.db.commit()
            await self.db.refresh(slot)

            logger.info(f"✅ Added build {build_id} to team {team_id}")
            return slot

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error adding build to team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add build to team: {str(e)}"
            )

    async def remove_build_from_team(self, team_id: str, slot_id: str, user: UserDB) -> bool:
        """
        Remove a build from a team composition.

        Args:
            team_id: Team ID
            slot_id: Team slot ID to remove
            user: Current user

        Returns:
            True if removed successfully

        Raises:
            HTTPException: If team or slot not found, or user doesn't have permission
        """
        try:
            # Get the team
            team = await self.get_team(team_id, user)
            if not team:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

            # Check ownership
            if team.user_id != str(user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this team")

            # Get the slot
            stmt = select(TeamSlotDB).where(and_(TeamSlotDB.id == slot_id, TeamSlotDB.team_composition_id == team_id))
            result = await self.db.execute(stmt)
            slot = result.scalar_one_or_none()
            if not slot:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team slot not found")

            # Delete the slot
            await self.db.delete(slot)
            await self.db.commit()

            logger.info(f"✅ Removed slot {slot_id} from team {team_id}")
            return True

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error removing build from team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to remove build from team: {str(e)}"
            )

    async def count_user_teams(self, user: UserDB) -> int:
        """
        Count total teams for a user.

        Args:
            user: User to count teams for

        Returns:
            Total number of teams
        """
        try:
            stmt = select(func.count(TeamCompositionDB.id)).where(TeamCompositionDB.user_id == str(user.id))
            result = await self.db.execute(stmt)
            return result.scalar_one()

        except Exception as e:
            logger.error(f"❌ Error counting teams for user {user.username}: {e}")
            return 0
