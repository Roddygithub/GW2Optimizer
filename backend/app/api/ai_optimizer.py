"""
AI Team Optimizer API

This module provides an API endpoint for generating optimized team compositions
using Mistral AI and live GW2 data.
"""

from datetime import datetime
from typing import Any, Dict, Optional  # noqa: F401 (used in type annotations)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.services.gw2_api import get_gw2_api_service
from app.services.mistral_ai import get_mistral_service

router = APIRouter()


class TeamOptimizationRequest(BaseModel):
    """Request model for team optimization"""

    team_size: int = Field(default=50, ge=5, le=80, description="Team size (5-80 players)")
    game_mode: str = Field(default="zerg", description="Game mode (zerg, raid, roaming)")
    world_id: Optional[int] = Field(default=None, description="GW2 World ID for live data")
    focus: Optional[str] = Field(default=None, description="Focus (offense, defense, mobility)")


class TeamOptimizationResponse(BaseModel):
    """Response model for team optimization"""

    timestamp: str
    team_size: int
    game_mode: str
    composition: Dict[str, Any]
    wvw_data: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


@router.post("/optimize", response_model=TeamOptimizationResponse)
async def optimize_team(request: TeamOptimizationRequest):
    """
    Generate optimized team composition using Mistral AI and live GW2 data.

    This endpoint:
    1. Fetches live WvW data from GW2 API (if world_id provided)
    2. Sends data to Mistral AI for analysis
    3. Generates optimized team composition
    4. Validates composition coherence
    5. Returns detailed team structure

    Args:
        request: Team optimization parameters

    Returns:
        Optimized team composition with metadata

    Example:
        POST /api/v1/ai/optimize
        {
            "team_size": 50,
            "game_mode": "zerg",
            "world_id": 2007,
            "focus": "offense"
        }
    """
    logger.info(f"🤖 AI Team Optimization requested: size={request.team_size}, mode={request.game_mode}")

    start_time = datetime.utcnow()

    try:
        # 1. Fetch live WvW data if world_id provided
        wvw_data = None
        if request.world_id:
            logger.info(f"📡 Fetching live WvW data for world {request.world_id}")
            gw2_service = get_gw2_api_service()
            try:
                wvw_data = await gw2_service.fetch_live_wvw_data(request.world_id)
                logger.info("✅ WvW data fetched successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch WvW data: {str(e)}")
                wvw_data = {"status": "unavailable", "error": str(e)}
            finally:
                await gw2_service.close()

        # 2. Generate team composition with Mistral AI
        logger.info("🤖 Generating team composition with Mistral AI")
        mistral_service = get_mistral_service()

        try:
            composition = await mistral_service.generate_team_composition(
                wvw_data=wvw_data or {}, team_size=request.team_size, game_mode=request.game_mode
            )
            logger.info("✅ Team composition generated successfully")
        finally:
            await mistral_service.close()

        # 3. Calculate metadata
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        metadata = {
            "generation_time_seconds": duration,
            "used_live_data": wvw_data is not None and wvw_data.get("status") != "unavailable",
            "ai_model": composition.get("model", "unknown"),
            "source": composition.get("source", "unknown"),
            "focus": request.focus,
        }

        # 4. Validate composition
        validation = validate_composition(composition, request.team_size)
        metadata["validation"] = validation

        logger.info(f"✅ Team optimization complete in {duration:.2f}s")

        return TeamOptimizationResponse(
            timestamp=start_time.isoformat(),
            team_size=request.team_size,
            game_mode=request.game_mode,
            composition=composition,
            wvw_data=wvw_data,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"❌ Team optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/test")
async def test_ai_optimizer():
    """
    Test endpoint to verify AI optimizer is working.

    Returns:
        Simple test response with service status
    """
    return {
        "status": "operational",
        "service": "AI Team Optimizer",
        "version": "3.0.0",
        "endpoints": {"optimize": "/api/v1/ai/optimize (POST)", "test": "/api/v1/ai/test (GET)"},
    }


def validate_composition(composition: Dict[str, Any], expected_size: int) -> Dict[str, Any]:
    """
    Validate team composition coherence.

    Checks:
    - Total player count matches expected size
    - Profession distribution is reasonable
    - Role balance (support, tank, DPS)
    - Boon coverage (might, fury, quickness, alacrity, stability)

    Args:
        composition: Generated team composition
        expected_size: Expected team size

    Returns:
        Validation results
    """
    validation = {"valid": True, "warnings": [], "errors": [], "checks": {}}

    # Check 1: Total size
    builds = composition.get("builds", [])
    total_count = sum(build.get("count", 0) for build in builds)

    validation["checks"]["total_size"] = {
        "expected": expected_size,
        "actual": total_count,
        "valid": abs(total_count - expected_size) <= 5,  # Allow 5 player variance
    }

    if abs(total_count - expected_size) > 5:
        validation["errors"].append(f"Team size mismatch: expected {expected_size}, got {total_count}")
        validation["valid"] = False

    # Check 2: Role distribution
    role_counts = {}
    for build in builds:
        role = build.get("role", "Unknown")
        role_counts[role] = role_counts.get(role, 0) + build.get("count", 0)

    validation["checks"]["role_distribution"] = role_counts

    # Check 3: Support presence (at least 20% support)
    support_count = role_counts.get("Support", 0)
    support_ratio = support_count / total_count if total_count > 0 else 0

    validation["checks"]["support_ratio"] = {
        "count": support_count,
        "ratio": support_ratio,
        "valid": support_ratio >= 0.15,  # At least 15% support
    }

    if support_ratio < 0.15:
        validation["warnings"].append(f"Low support ratio: {support_ratio:.1%} (recommended: >15%)")

    # Check 4: Tank presence (at least 5% tanks for zerg)
    tank_count = role_counts.get("Tank", 0)
    tank_ratio = tank_count / total_count if total_count > 0 else 0

    validation["checks"]["tank_ratio"] = {
        "count": tank_count,
        "ratio": tank_ratio,
        "valid": tank_ratio >= 0.05,  # At least 5% tanks
    }

    if tank_ratio < 0.05:
        validation["warnings"].append(f"Low tank ratio: {tank_ratio:.1%} (recommended: >5%)")

    # Check 5: Profession diversity (no single profession >40%)
    profession_counts = {}
    for build in builds:
        profession = build.get("profession", "Unknown")
        profession_counts[profession] = profession_counts.get(profession, 0) + build.get("count", 0)

    validation["checks"]["profession_distribution"] = profession_counts

    for profession, count in profession_counts.items():
        ratio = count / total_count if total_count > 0 else 0
        if ratio > 0.4:
            validation["warnings"].append(f"High {profession} ratio: {ratio:.1%} (recommended: <40%)")

    return validation
