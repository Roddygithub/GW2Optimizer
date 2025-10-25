"""Build API endpoints with database persistence."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user as get_current_user
from app.core.cache import cacheable, invalidate_cache
from app.core.logging import logger
from app.db.base import get_db
from app.learning.data.collector import InteractionCollector
from app.models.build import (
    Build,
    BuildCreate,
    BuildDB,
    BuildResponse,
    BuildUpdate,
    Equipment,
    GameMode,
    Profession,
    Role,
    Skill,
    TraitLine,
)
from app.db.models import UserDB
from app.services.build_service_db import BuildService

router = APIRouter()


def build_db_to_pydantic(build_db: BuildDB) -> Build:
    """Convert BuildDB to Pydantic Build model."""
    return Build(
        id=build_db.id,
        user_id=str(build_db.user_id),
        name=build_db.name,
        profession=Profession(build_db.profession) if isinstance(build_db.profession, str) else build_db.profession,
        specialization=build_db.specialization,
        game_mode=GameMode(build_db.game_mode) if isinstance(build_db.game_mode, str) else build_db.game_mode,
        role=Role(build_db.role) if isinstance(build_db.role, str) else build_db.role,
        description=build_db.description,
        playstyle=build_db.playstyle,
        source_url=build_db.source_url,
        source_type=build_db.source_type,
        effectiveness=build_db.effectiveness,
        difficulty=build_db.difficulty,
        is_public=build_db.is_public,
        trait_lines=[TraitLine(**tl) if isinstance(tl, dict) else tl for tl in (build_db.trait_lines or [])],
        skills=[Skill(**s) if isinstance(s, dict) else s for s in (build_db.skills or [])],
        equipment=[Equipment(**e) if isinstance(e, dict) else e for e in (build_db.equipment or [])],
        synergies=build_db.synergies or [],
        counters=build_db.counters or [],
        created_at=build_db.created_at,
        updated_at=build_db.updated_at,
    )


@router.post("/", response_model=Build, status_code=status.HTTP_201_CREATED)
async def create_build(
    build_data: BuildCreate, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Build:
    """
    Create a new build for the authenticated user.

    Args:
        build_data: Build creation data
        current_user: Authenticated user
        db: Database session

    Returns:
        Created build

    Example:
        ```json
        {
            "name": "Firebrand Support",
            "profession": "Guardian",
            "specialization": "Firebrand",
            "game_mode": "zerg",
            "role": "support",
            "description": "Boon support build for zergs",
            "is_public": true,
            "trait_lines": [...],
            "skills": [...],
            "equipment": [...]
        }
        ```
    """
    try:
        service = BuildService(db)
        build_db = await service.create_build(build_data, current_user)

        # Collect interaction for learning
        try:
            collector = InteractionCollector()
            await collector.collect_build_creation(build_db.__dict__, user_id=str(current_user.id))
        except Exception as e:
            logger.warning(f"Failed to collect interaction: {e}")

        # Convert to Pydantic model
        return build_db_to_pydantic(build_db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating build: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating build: {str(e)}")


@router.get("/{build_id}", response_model=Build)
@cacheable("build:{build_id}", ttl=3600)
async def get_build(
    build_id: str, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Build:
    """
    Get a specific build by ID.

    Returns the build if:
    - It belongs to the authenticated user, OR
    - It is marked as public

    Args:
        build_id: Build ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Build details
    """
    try:
        service = BuildService(db)
        build_db = await service.get_build(build_id, current_user)

        if not build_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

        return build_db_to_pydantic(build_db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching build: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching build: {str(e)}")


@router.get("/", response_model=List[Build])
async def list_user_builds(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records"),
    profession: Optional[Profession] = Query(None, description="Filter by profession"),
    game_mode: Optional[GameMode] = Query(None, description="Filter by game mode"),
    role: Optional[Role] = Query(None, description="Filter by role"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Build]:
    """
    List builds for the authenticated user with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        profession: Filter by profession
        game_mode: Filter by game mode
        role: Filter by role
        is_public: Filter by public status
        current_user: Authenticated user
        db: Database session

    Returns:
        List of builds
    """
    try:
        service = BuildService(db)
        builds_db = await service.list_user_builds(
            user=current_user,
            skip=skip,
            limit=limit,
            profession=profession,
            game_mode=game_mode,
            role=role,
            is_public=is_public,
        )

        return [build_db_to_pydantic(build) for build in builds_db]

    except Exception as e:
        logger.error(f"Error listing builds: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error listing builds: {str(e)}")


@router.get("/public/all", response_model=List[Build])
@cacheable("builds:public:{profession}:{game_mode}:{role}", ttl=1800)
async def list_public_builds(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records"),
    profession: Optional[Profession] = Query(None, description="Filter by profession"),
    game_mode: Optional[GameMode] = Query(None, description="Filter by game mode"),
    role: Optional[Role] = Query(None, description="Filter by role"),
    db: AsyncSession = Depends(get_db),
) -> List[Build]:
    """
    List public builds (no authentication required).

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        profession: Filter by profession
        game_mode: Filter by game mode
        role: Filter by role
        db: Database session

    Returns:
        List of public builds
    """
    try:
        service = BuildService(db)
        builds_db = await service.list_public_builds(
            skip=skip, limit=limit, profession=profession, game_mode=game_mode, role=role
        )

        return [build_db_to_pydantic(build) for build in builds_db]

    except Exception as e:
        logger.error(f"Error listing public builds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error listing public builds: {str(e)}"
        )


@router.put("/builds/{build_id}", response_model=Build)
@invalidate_cache("build:{build_id}")
async def update_build(
    build_id: str,
    build_data: BuildUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Build:
    """
    Update a build.

    Only the build owner can update it.

    Args:
        build_id: Build ID to update
        build_data: Updated build data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated build
    """
    try:
        service = BuildService(db)
        build_db = await service.update_build(build_id, build_data, current_user)

        if not build_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build not found")

        return build_db_to_pydantic(build_db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating build: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating build: {str(e)}")


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
@invalidate_cache("build:{build_id}")
async def delete_build(
    build_id: str, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a build.

    Only the build owner can delete it.
    Cascade delete will remove all related team slots.

    Args:
        build_id: Build ID to delete
        current_user: Authenticated user
        db: Database session
    """
    try:
        service = BuildService(db)
        await service.delete_build(build_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting build: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting build: {str(e)}")


@router.get("/stats/count", response_model=dict)
async def get_build_count(current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get the total number of builds for the authenticated user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Dictionary with build count
    """
    try:
        service = BuildService(db)
        count = await service.count_user_builds(current_user)

        return {"count": count, "user_id": str(current_user.id)}

    except Exception as e:
        logger.error(f"Error counting builds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error counting builds: {str(e)}"
        )
