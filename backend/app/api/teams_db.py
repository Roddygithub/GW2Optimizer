"""Team composition API endpoints with database persistence."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user as get_current_user
from app.core.cache import cacheable, invalidate_cache
from app.core.logging import logger
from app.db.base import get_db
from app.learning.data.collector import InteractionCollector
from app.models.build import GameMode
from app.models.team import (
    TeamComposition,
    TeamCompositionCreate,
    TeamCompositionDB,
    TeamCompositionUpdate,
    TeamResponse,
    TeamSlot,
    TeamSynergy,
)
from app.models.build import Build
from app.db.models import UserDB
from app.services.team_service_db import TeamService
from app.api.builds_db import build_db_to_pydantic

router = APIRouter()


def team_db_to_pydantic(team_db: TeamCompositionDB) -> TeamComposition:
    """Convert TeamCompositionDB to Pydantic TeamComposition model."""
    # Convert team slots
    slots = []
    for slot_db in team_db.team_slots or []:
        if slot_db.build:
            slots.append(
                TeamSlot(
                    id=slot_db.id,
                    slot_number=slot_db.slot_number,
                    build=build_db_to_pydantic(slot_db.build),
                    player_name=slot_db.player_name,
                    priority=slot_db.priority,
                )
            )

    # Convert synergies
    synergies = []
    for syn in team_db.synergies or []:
        if isinstance(syn, dict):
            synergies.append(TeamSynergy(**syn))
        else:
            synergies.append(syn)

    return TeamComposition(
        id=team_db.id,
        user_id=team_db.user_id,
        name=team_db.name,
        game_mode=GameMode(team_db.game_mode) if isinstance(team_db.game_mode, str) else team_db.game_mode,
        team_size=team_db.team_size,
        description=team_db.description,
        is_public=team_db.is_public,
        slots=slots,
        synergies=synergies,
        weaknesses=team_db.weaknesses or [],
        strengths=team_db.strengths or [],
        overall_rating=team_db.overall_rating,
        created_at=team_db.created_at,
        updated_at=team_db.updated_at,
    )


@router.post("/teams", response_model=TeamComposition, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCompositionCreate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamComposition:
    """
    Create a new team composition for the authenticated user.

    Args:
        team_data: Team creation data
        current_user: Authenticated user
        db: Database session

    Returns:
        Created team composition

    Example:
        ```json
        {
            "name": "Zerg Composition",
            "game_mode": "zerg",
            "team_size": 15,
            "description": "Standard zerg composition",
            "is_public": true,
            "build_ids": [
                "build-id-1",
                "build-id-2",
                "build-id-3"
            ]
        }
        ```
    """
    try:
        service = TeamService(db)
        team_db = await service.create_team(team_data, current_user)

        # Collect interaction for learning
        try:
            collector = InteractionCollector()
            await collector.collect_team_creation(team_db.__dict__, user_id=str(current_user.id))
        except Exception as e:
            logger.warning(f"Failed to collect interaction: {e}")

        # Convert to Pydantic model
        return team_db_to_pydantic(team_db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating team: {str(e)}")


@router.get("/teams/{team_id}", response_model=TeamComposition)
@cacheable("team:{team_id}", ttl=3600)
async def get_team(
    team_id: str, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> TeamComposition:
    """
    Get a specific team composition by ID.

    Returns the team if:
    - It belongs to the authenticated user, OR
    - It is marked as public

    Args:
        team_id: Team ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Team composition details
    """
    try:
        service = TeamService(db)
        team_db = await service.get_team(team_id, current_user)

        if not team_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        return team_db_to_pydantic(team_db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching team: {str(e)}")


@router.get("/teams", response_model=List[TeamComposition])
async def list_user_teams(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records"),
    game_mode: Optional[GameMode] = Query(None, description="Filter by game mode"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[TeamComposition]:
    """
    List team compositions for the authenticated user with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        game_mode: Filter by game mode
        is_public: Filter by public status
        current_user: Authenticated user
        db: Database session

    Returns:
        List of team compositions
    """
    try:
        service = TeamService(db)
        teams_db = await service.list_user_teams(
            user=current_user, skip=skip, limit=limit, game_mode=game_mode, is_public=is_public
        )

        return [team_db_to_pydantic(team) for team in teams_db]

    except Exception as e:
        logger.error(f"Error listing teams: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error listing teams: {str(e)}")


@router.get("/teams/public/all", response_model=List[TeamComposition])
@cacheable("teams:public:{game_mode}", ttl=1800)
async def list_public_teams(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records"),
    game_mode: Optional[GameMode] = Query(None, description="Filter by game mode"),
    db: AsyncSession = Depends(get_db),
) -> List[TeamComposition]:
    """
    List public team compositions (no authentication required).

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        game_mode: Filter by game mode
        db: Database session

    Returns:
        List of public team compositions
    """
    try:
        service = TeamService(db)
        teams_db = await service.list_public_teams(skip=skip, limit=limit, game_mode=game_mode)

        return [team_db_to_pydantic(team) for team in teams_db]

    except Exception as e:
        logger.error(f"Error listing public teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error listing public teams: {str(e)}"
        )


@router.put("/teams/{team_id}", response_model=TeamComposition)
@invalidate_cache("team:{team_id}")
async def update_team(
    team_id: str,
    team_data: TeamCompositionUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamComposition:
    """
    Update a team composition.

    Only the team owner can update it.

    Args:
        team_id: Team ID to update
        team_data: Updated team data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated team composition
    """
    try:
        service = TeamService(db)
        team_db = await service.update_team(team_id, team_data, current_user)

        if not team_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        return team_db_to_pydantic(team_db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating team: {str(e)}")


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
@invalidate_cache("team:{team_id}")
async def delete_team(
    team_id: str, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a team composition.

    Only the team owner can delete it.
    Cascade delete will remove all related team slots.

    Args:
        team_id: Team ID to delete
        current_user: Authenticated user
        db: Database session
    """
    try:
        service = TeamService(db)
        await service.delete_team(team_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting team: {str(e)}")


@router.post("/teams/{team_id}/builds/{build_id}", response_model=TeamComposition)
@invalidate_cache("team:{team_id}")
async def add_build_to_team(
    team_id: str,
    build_id: str,
    slot_number: Optional[int] = Query(None, ge=1, le=50, description="Slot number"),
    player_name: Optional[str] = Query(None, max_length=100, description="Player name"),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamComposition:
    """
    Add a build to a team composition.

    Args:
        team_id: Team ID
        build_id: Build ID to add
        slot_number: Optional slot number (auto-assigned if not provided)
        player_name: Optional player name for the slot
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message with slot details
    """
    try:
        service = TeamService(db)
        team = await service.add_build_to_team(
            team_id=team_id, build_id=build_id, user=current_user, slot_number=slot_number, player_name=player_name
        )

        return team_db_to_pydantic(team)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding build to team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error adding build to team: {str(e)}"
        )


@router.delete("/teams/{team_id}/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
@invalidate_cache("team:{team_id}")
async def remove_build_from_team(
    team_id: str, slot_id: str, current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove a build from a team composition.

    Args:
        team_id: Team ID
        slot_id: Team slot ID to remove
        current_user: Authenticated user
        db: Database session
    """
    try:
        service = TeamService(db)
        await service.remove_build_from_team(team_id, slot_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing build from team: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error removing build from team: {str(e)}"
        )


@router.get("/teams/stats/count", response_model=dict)
async def get_team_count(current_user: UserDB = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get the total number of teams for the authenticated user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Dictionary with team count
    """
    try:
        service = TeamService(db)
        count = await service.count_user_teams(current_user)

        return {"count": count, "user_id": str(current_user.id)}

    except Exception as e:
        logger.error(f"Error counting teams: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error counting teams: {str(e)}")
