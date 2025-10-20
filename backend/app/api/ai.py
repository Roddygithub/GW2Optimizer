"""AI API endpoints for agents and workflows."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.core.logging import logger
from app.services.ai_service import AIService
from app.db.models import User
from app.api.auth import get_current_active_user

router = APIRouter()


@router.post(
    "/recommend-build",
    response_model=Dict[str, Any],
    summary="Recommend Build",
    description="Get build recommendations using the RecommenderAgent",
    dependencies=[Depends(get_current_active_user)],
)
async def recommend_build(
    request: Dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get build recommendations for a specific profession and role.

    Request body:
    - profession: str - Character profession (Guardian, Warrior, etc.)
    - role: str - Desired role (DPS, Support, Tank, Hybrid)
    - game_mode: str - Game mode (PvE, PvP, WvW, Raids, Fractals, Strikes)
    - context: str - Optional additional context
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.run_agent("recommender", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error recommending build: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service error: {str(e)}")


@router.post(
    "/analyze-team-synergy",
    response_model=Dict[str, Any],
    summary="Analyze Team Synergy",
    description="Analyze team composition synergy using the SynergyAgent",
    dependencies=[Depends(get_current_active_user)],
)
async def analyze_team_synergy(
    request: Dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Analyze the synergy of a team composition.

    Request body:
    - professions: List[str] - List of team professions
    - game_mode: str - Game mode
    - squad_size: int - Optional squad size (default: 5)
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.run_agent("synergy", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error analyzing team synergy: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service error: {str(e)}")


@router.post(
    "/optimize-team",
    response_model=Dict[str, Any],
    summary="Optimize Team Composition",
    description="Optimize a team composition using the OptimizerAgent",
    dependencies=[Depends(get_current_active_user)],
)
async def optimize_team(
    request: Dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Optimize a team composition.

    Request body:
    - current_composition: List[str] - Current team professions
    - objectives: List[str] - Optimization objectives (maximize_boons, maximize_dps, etc.)
    - game_mode: str - Game mode (PvE, PvP, WvW, Raids, Fractals, Strikes)
    - max_changes: int - Maximum number of changes allowed (default: 3)
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.run_agent("optimizer", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error optimizing team: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service error: {str(e)}")


@router.post(
    "/workflow/build-optimization",
    response_model=Dict[str, Any],
    summary="Execute Build Optimization Workflow",
    description="Execute the complete build optimization workflow",
    dependencies=[Depends(get_current_active_user)],
)
async def execute_build_optimization(
    request: Dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Execute the complete build optimization workflow.

    This workflow:
    1. Generates initial build recommendation
    2. Analyzes synergy with team (if provided)
    3. Generates alternative build variants

    Request body:
    - profession: str - Character profession
    - role: str - Desired role
    - game_mode: str - Game mode
    - team_composition: List[str] - Optional team composition
    - optimization_iterations: int - Number of optimization iterations (default: 2)
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.execute_workflow("build_optimization", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error executing build optimization workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Workflow execution error: {str(e)}"
        )


@router.post(
    "/workflow/team-analysis",
    response_model=Dict[str, Any],
    summary="Execute Team Analysis Workflow",
    description="Execute the complete team analysis workflow",
    dependencies=[Depends(get_current_active_user)],
)
async def execute_team_analysis(
    request: Dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Execute the complete team analysis workflow.

    This workflow:
    1. Analyzes current team synergy
    2. Optimizes composition (if requested)
    3. Compares before/after
    4. Provides detailed recommendations

    Request body:
    - professions: List[str] - Team professions
    - game_mode: str - Game mode
    - optimize: bool - Whether to optimize the composition (default: False)
    - max_changes: int - Maximum changes for optimization (default: 2)
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.execute_workflow("team_analysis", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error executing team analysis workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Workflow execution error: {str(e)}"
        )


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Get AI Service Status",
    description="Get the current status of the AI service and registered agents/workflows",
)
async def get_ai_status() -> Dict[str, Any]:
    """
    Get the current status of the AI service.

    Returns information about:
    - Registered agents
    - Registered workflows
    - Service health
    """
    try:
        ai_service = AIService()
        status_info = ai_service.get_service_status()
        return status_info
    except Exception as e:
        logger.error(f"Error getting AI service status: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Service status error: {str(e)}")
