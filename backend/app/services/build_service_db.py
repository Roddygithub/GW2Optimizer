"""Build service with database persistence for GW2Optimizer."""

from typing import List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.build import Build, BuildCreate, BuildDB, BuildUpdate, GameMode, Profession, Role
from app.db.models import UserDB
from app.models.learning import DataSource
from app.services.learning.data_collector import DataCollector


class BuildService:
    """Service for managing builds with database persistence."""

    def __init__(self, db: AsyncSession):
        """
        Initialize build service.

        Args:
            db: Async database session
        """
        self.db = db
        self.collector = DataCollector()

    async def create_build(self, build_data: BuildCreate, user: UserDB) -> BuildDB:
        """
        Create a new build for the specified user.

        Args:
            build_data: Build creation data
            user: User creating the build

        Returns:
            Created build from database

        Raises:
            HTTPException: If build creation fails
        """
        try:
            # Convert Pydantic model to dict
            build_dict = build_data.model_dump(exclude_unset=True)

            # Create database model
            build_db = BuildDB(id=str(uuid4()), user_id=str(user.id), **build_dict)

            self.db.add(build_db)
            await self.db.commit()
            await self.db.refresh(build_db)

            logger.info(f"✅ Created build {build_db.id} for user {user.id}")
            try:
                build_model = Build.model_validate(build_db)
                await self.collector.collect_build(build_model, source=DataSource.USER_IMPORT)
            except Exception as e:
                logger.error(
                    "Failed to collect user build for learning",
                    extra={"build_id": build_db.id, "user_id": str(user.id), "error": str(e)},
                )

            return build_db

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error creating build: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create build: {str(e)}"
            )

    async def get_build(self, build_id: str, user: UserDB) -> BuildDB:
        """
        Get a build by ID if it belongs to the user or is public.

        Args:
            build_id: Build ID
            user: Current user

        Returns:
            Build if found and accessible

        Raises:
            HTTPException: 404 if build not found, 403 if not authorized
        """
        try:
            # Check if build exists and is accessible
            stmt = select(BuildDB).where(BuildDB.id == build_id)
            result = await self.db.execute(stmt)
            build = result.scalar_one_or_none()

            # Return 404 if build doesn't exist OR if it's private and user doesn't own it
            # This prevents revealing the existence of private builds
            if not build or (str(build.user_id) != str(user.id) and not build.is_public):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

            return build

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error getting build {build_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get build: {str(e)}"
            )

    async def list_user_builds(
        self,
        user: UserDB,
        skip: int = 0,
        limit: int = 100,
        profession: Optional[Profession] = None,
        game_mode: Optional[GameMode] = None,
        role: Optional[Role] = None,
        is_public: Optional[bool] = None,
    ) -> List[BuildDB]:
        """
        List builds for a user with optional filters.

        Args:
            user: User whose builds to list
            skip: Number of records to skip
            limit: Maximum number of records to return
            profession: Filter by profession
            game_mode: Filter by game mode
            role: Filter by role
            is_public: Filter by public status

        Returns:
            List of builds
        """
        try:
            stmt = select(BuildDB).where(BuildDB.user_id == str(user.id))

            # Apply filters
            if profession:
                stmt = stmt.where(BuildDB.profession == profession.value)
            if game_mode:
                stmt = stmt.where(BuildDB.game_mode == game_mode.value)
            if role:
                stmt = stmt.where(BuildDB.role == role.value)
            if is_public is not None:
                stmt = stmt.where(BuildDB.is_public == is_public)

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit).order_by(BuildDB.created_at.desc())

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Error listing builds for user {user.username}: {e}")
            return []

    async def list_public_builds(
        self,
        skip: int = 0,
        limit: int = 100,
        profession: Optional[Profession] = None,
        game_mode: Optional[GameMode] = None,
        role: Optional[Role] = None,
    ) -> List[BuildDB]:
        """
        List public builds with optional filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            profession: Filter by profession
            game_mode: Filter by game mode
            role: Filter by role

        Returns:
            List of public builds
        """
        try:
            stmt = select(BuildDB).where(BuildDB.is_public == True)

            # Apply filters
            if profession:
                stmt = stmt.where(BuildDB.profession == profession.value)
            if game_mode:
                stmt = stmt.where(BuildDB.game_mode == game_mode.value)
            if role:
                stmt = stmt.where(BuildDB.role == role.value)

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit).order_by(BuildDB.created_at.desc())

            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"❌ Error listing public builds: {e}")
            return []

    async def update_build(self, build_id: str, build_data: BuildUpdate, user: UserDB) -> Optional[BuildDB]:
        """
        Update a build if it belongs to the user.

        Args:
            build_id: Build ID to update
            build_data: Updated build data
            user: Current user

        Returns:
            Updated build if successful, None otherwise

        Raises:
            HTTPException: If build not found or user doesn't have permission
        """
        try:
            # Check if build exists first (404)
            stmt = select(BuildDB).where(BuildDB.id == build_id)
            result = await self.db.execute(stmt)
            build = result.scalar_one_or_none()

            # Return 404 if build doesn't exist OR if user doesn't own it
            # This prevents revealing the existence of builds owned by others
            if not build or str(build.user_id) != str(user.id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

            # Update fields
            update_data = build_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(build, field, value)

            await self.db.commit()
            await self.db.refresh(build)

            logger.info(f"✅ Updated build {build_id} for user {user.id}")
            return build

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error updating build {build_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update build: {str(e)}"
            )

    async def delete_build(self, build_id: str, user: UserDB) -> bool:
        """
        Delete a build if it belongs to the user.

        Args:
            build_id: Build ID to delete
            user: Current user

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If build not found or user doesn't have permission
        """
        try:
            # Check if build exists
            stmt = select(BuildDB).where(BuildDB.id == build_id)
            result = await self.db.execute(stmt)
            build = result.scalar_one_or_none()

            # Return 404 if build doesn't exist OR if user doesn't own it
            # This prevents revealing the existence of builds owned by others
            if not build or str(build.user_id) != str(user.id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

            # Delete the build (cascade will handle related records)
            await self.db.delete(build)
            await self.db.commit()

            logger.info(f"✅ Deleted build {build_id} for user {user.id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Error deleting build {build_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete build: {str(e)}"
            )

    async def count_user_builds(self, user: UserDB) -> int:
        """
        Count total builds for a user.

        Args:
            user: User to count builds for

        Returns:
            Total number of builds
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count(BuildDB.id)).where(BuildDB.user_id == str(user.id))
            result = await self.db.execute(stmt)
            return result.scalar_one()

        except Exception as e:
            logger.error(f"❌ Error counting builds for user {user.username}: {e}")
            return 0


# Compatibility alias: preserve historic import name used across the codebase
BuildServiceDB = BuildService
