"""Team composition API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import logger
from app.models.build import GameMode
from app.models.team import TeamComposition, TeamOptimizeRequest, TeamResponse
from app.services.team_service import TeamService

router = APIRouter()
team_service = TeamService()


@router.post("/teams/optimize", response_model=TeamResponse)
async def optimize_team(request: TeamOptimizeRequest) -> TeamResponse:
    """
    Optimize a team composition based on requirements.

    The AI will:
    - Analyze role requirements
    - Select optimal builds
    - Maximize synergies
    - Consider game mode meta
    """
    try:
        logger.info(
            f"Optimizing team: {request.game_mode} - " f"Size: {request.team_size} - Roles: {request.required_roles}"
        )
        response = await team_service.optimize_team(request)
        return response
    except Exception as e:
        logger.error(f"Error optimizing team: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing team: {str(e)}")


@router.get("/teams/{team_id}", response_model=TeamComposition)
async def get_team(team_id: str) -> TeamComposition:
    """Get a specific team composition by ID."""
    try:
        team = await team_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching team: {str(e)}")


@router.get("/teams", response_model=List[TeamComposition])
async def list_teams(
    game_mode: Optional[GameMode] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> List[TeamComposition]:
    """List team compositions with optional filters."""
    try:
        teams = await team_service.list_teams(game_mode=game_mode, limit=limit)
        return teams
    except Exception as e:
        logger.error(f"Error listing teams: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing teams: {str(e)}")


@router.post("/teams/{team_id}/analyze")
async def analyze_team(team_id: str) -> TeamResponse:
    """
    Analyze an existing team composition.

    Provides:
    - Synergy analysis
    - Weakness identification
    - Improvement suggestions
    """
    try:
        team = await team_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        response = await team_service.analyze_team(team)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing team: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing team: {str(e)}")
