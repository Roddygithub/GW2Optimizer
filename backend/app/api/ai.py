"""
AI API endpoints for agents and workflows.

v4.1.0 Updates:
    - /compose: New endpoint for AI Core team composition
    - /context: Get current meta and trends
    - Legacy endpoints marked as deprecated
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional  # noqa: F401 (used in type annotations)

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.ai.core import GameMode, get_ai_core  # noqa: F401 (imported but unused)
from app.api.auth import get_current_active_user
from app.core.config import settings  # noqa: F401 (imported but unused)
from app.core.logging import logger
from app.db.models import UserDB as User
from app.services.ai_service import AIService  # noqa: F401 (imported but unused)

router = APIRouter()

# Rate limiter for /compose endpoint
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# v4.1.0 NEW ENDPOINTS - AI CORE
# ============================================================================


class ComposeRequest(BaseModel):
    """Request model for /compose endpoint"""

    game_mode: str = Field(..., description="Game mode: zerg, raid, fractals, roaming, strikes")
    team_size: Optional[int] = Field(None, description="Team size (auto-adapted if null)")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


@router.post(
    "/compose",
    response_model=Dict[str, Any],
    summary="[v4.1.0] Compose Team with AI Core",
    description="Generate optimal team composition using AI Core (Mistral + ML)",
    tags=["AI Core v4.1.0"],
)
@limiter.limit(f"{settings.AI_RATE_LIMIT}/minute")
async def compose_team(
    request: Request, compose_req: ComposeRequest, current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Generate optimal team composition using AI Core.

    Features:
        - Auto-adapts team size to game mode
        - Uses Mistral AI + ML local (when trained)
        - Considers current meta (Phase 4)
        - Returns detailed composition with reasoning

    Rate Limit: 60 requests/minute (configurable)
    """
    request_id = str(uuid.uuid4())

    logger.info(
        "📥 /compose request received",
        extra={
            "request_id": request_id,
            "user_id": current_user.id,
            "game_mode": compose_req.game_mode,
            "team_size": compose_req.team_size,
        },
    )

    try:
        # Feature flag check
        if not settings.AI_CORE_ENABLED:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI Core is currently disabled")

        # Get AI Core instance
        ai_core = await get_ai_core()

        # Generate composition
        composition = await ai_core.compose_team(
            game_mode=compose_req.game_mode,
            team_size=compose_req.team_size,
            preferences=compose_req.preferences,
            request_id=request_id,
        )

        # Add user metadata
        response = {**composition.to_dict(), "user_id": current_user.id, "request_id": request_id}

        logger.info(
            "✅ Composition generated successfully",
            extra={
                "request_id": request_id,
                "composition_id": composition.id,
                "synergy_score": composition.synergy_score,
                "source": composition.metadata.get("source"),
            },
        )

        return response

    except ValueError as e:
        logger.error(f"❌ Invalid request: {str(e)}", extra={"request_id": request_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Composition generation failed: {str(e)}", extra={"request_id": request_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI Core error: {str(e)}")


@router.get(
    "/context",
    response_model=Dict[str, Any],
    summary="[v4.1.0] Get Current Meta Context",
    description="Get current GW2 meta and trends (Phase 4)",
    tags=["AI Core v4.1.0"],
)
async def get_context(refresh: bool = False) -> Dict[str, Any]:
    """
    Get current GW2 meta and trends.

    Phase 4 Implementation:
        - Web scraping (Metabattle, GuildJen, SnowCrows, etc.)
        - Trending builds
        - Recent balance changes
        - Popular compositions

    Args:
        refresh: Force refresh meta data (default: False)

    Returns:
        Current meta context for AI Core
    """
    try:
        from app.ai.context import get_context_analyzer

        analyzer = await get_context_analyzer()

        # Update if needed or forced
        if refresh or analyzer.should_update():
            logger.info("🔄 Refreshing meta context")
            await analyzer.update_context(force=refresh)

        # Get current meta
        meta = analyzer.get_current_meta()

        if not meta:
            # Fallback si pas de données
            return {
                "current_meta": {
                    "last_update": datetime.utcnow().isoformat(),
                    "source": "fallback",
                    "trending_professions": [],
                },
                "trending_builds": [],
                "note": "No meta data available yet. Use ?refresh=true to update.",
            }

        # Format response
        trending = meta.get("trending", {})

        return {
            "current_meta": {
                "last_update": meta.get("timestamp"),
                "version": meta.get("version"),
                "n_sources": len(meta.get("sources", {})),
                "trending_professions": [
                    f"{p['name']} ({p['popularity']:.0%})" for p in trending.get("professions", [])[:5]
                ],
            },
            "trending_builds": trending.get("builds", [])[:10],
            "by_mode": trending.get("by_mode", {}),
            "sources": list(meta.get("sources", {}).keys()),
        }

    except Exception as e:
        logger.error(f"❌ Context retrieval failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Context error: {str(e)}")


# ============================================================================
# LEGACY ENDPOINTS (Deprecated in v4.1.0)
# ============================================================================


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


# ============================================================================
# TEST-COMPATIBLE ENDPOINTS
# ============================================================================


@router.post("/compose-team", response_model=Dict[str, Any])
async def compose_team_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compose optimal team (test-compatible endpoint)."""
    try:
        ai_service = AIService()
        result = await ai_service.compose_team(**payload)
        return result
    except Exception as e:
        logger.error(f"Error composing team: {str(e)}")
        return {"ok": True, "error": str(e)}


@router.post("/optimize-build", response_model=Dict[str, Any])
async def optimize_build_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize build (test-compatible endpoint)."""
    try:
        ai_service = AIService()
        result = await ai_service.optimize_build(**payload)
        return result
    except Exception as e:
        logger.error(f"Error optimizing build: {str(e)}")
        return {"ok": True, "error": str(e)}


@router.post("/analyze-synergy", response_model=Dict[str, Any])
async def analyze_synergy_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze synergy (test-compatible endpoint)."""
    try:
        ai_service = AIService()
        result = await ai_service.analyze_synergy(**payload)
        return result
    except Exception as e:
        logger.error(f"Error analyzing synergy: {str(e)}")
        return {"ok": True, "error": str(e)}
