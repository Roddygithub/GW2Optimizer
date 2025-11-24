from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from app.api.auth import get_current_active_user
from app.core.logging import logger
from app.db.models import UserDB as User
from app.services.skill_analysis_service import SkillAnalysisService
from app.services.build_analysis_service import BuildAnalysisService
from app.services.url_analysis_service import UrlAnalysisService


router = APIRouter()


class SkillAnalysisRequest(BaseModel):
    skill_id: int = Field(..., description="GW2 skill ID (numeric)", example=12345)
    context: str = Field("WvW Zerg", description="Analysis context (e.g. WvW, PvE, Roaming)")


class BuildAnalysisRequest(BaseModel):
    specialization_id: Optional[int] = Field(
        None,
        description="GW2 specialization ID (numeric)",
        example=62,
    )
    trait_ids: List[int] = Field(
        default_factory=list,
        description="List of selected trait IDs for the build",
        example=[2057, 2058, 2059],
    )
    skill_ids: List[int] = Field(
        default_factory=list,
        description="List of skill IDs used in the build (utilities, heal, elite)",
        example=[9153, 9154, 9155],
    )
    context: str = Field(
        "WvW Zerg",
        description="Analysis context (e.g. WvW Zerg, Roaming, PvE)",
    )


class UrlAnalysisRequest(BaseModel):
    url: HttpUrl = Field(..., description="Community build URL (Hardstuck, Snowcrows, GuildJen, GW2Mists, etc.)")
    context: str = Field(
        "WvW Zerg",
        description="Analysis context (e.g. WvW Zerg, Roaming, PvE)",
    )


@router.post(
    "/analyze/skill",
    response_model=Dict[str, Any],
    summary="Analyze a Guild Wars 2 skill with AI",
    description="Fetches a GW2 skill by ID and analyzes its viability using the AnalystAgent (Ollama-backed).",
)
async def analyze_skill_endpoint(
    payload: SkillAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    logger.info(
        "AI skill analysis request",
        extra={"skill_id": payload.skill_id, "context": payload.context, "user_id": current_user.id},
    )

    service = SkillAnalysisService()

    try:
        result = await service.analyze_skill(payload.skill_id, context=payload.context)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Skill analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI analysis failed: {e}",
        )


@router.post(
    "/analyze/build",
    response_model=Dict[str, Any],
    summary="Analyze a Guild Wars 2 build with AI",
    description=(
        "Analyzes the synergy of a build (specialization, traits, skills) using the "
        "AnalystAgent backed by Ollama."
    ),
)
async def analyze_build_endpoint(
    payload: BuildAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    logger.info(
        "AI build analysis request",
        extra={
            "specialization_id": payload.specialization_id,
            "trait_ids": payload.trait_ids,
            "skill_ids": payload.skill_ids,
            "context": payload.context,
            "user_id": current_user.id,
        },
    )

    service = BuildAnalysisService()

    try:
        result = await service.analyze_build_synergy(
            specialization_id=payload.specialization_id,
            trait_ids=payload.trait_ids,
            skill_ids=payload.skill_ids,
            context=payload.context,
        )
        return result
    except ValueError as e:
        # Erreurs de validation de build (IDs incohérents, spécialisation inconnue, ...)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Build analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI build analysis failed: {e}",
        )


@router.post(
    "/analyze/url",
    response_model=Dict[str, Any],
    summary="Analyze a Guild Wars 2 build URL with AI",
    description=(
        "Scrapes a community build URL, decodes the GW2 chat code and runs "
        "an AI synergy analysis on the resulting build."
    ),
)
async def analyze_url_endpoint(
    payload: UrlAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    logger.info(
        "AI URL build analysis request",
        extra={
            "url": str(payload.url),
            "context": payload.context,
            "user_id": current_user.id,
        },
    )

    service = UrlAnalysisService()

    try:
        result = await service.analyze_from_url(str(payload.url), context=payload.context)
        return result
    except ValueError as e:
        # Invalid chat code, unsupported URL, inconsistent build, etc.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"URL build analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI URL analysis failed: {e}",
        )
