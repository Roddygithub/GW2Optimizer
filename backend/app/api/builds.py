"""Build API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.logging import logger
from app.models.build import Build, BuildCreate, BuildResponse, GameMode, Profession, Role
from app.services.build_service import BuildService

router = APIRouter()
build_service = BuildService()


@router.post("/builds", response_model=BuildResponse)
async def create_build(request: BuildCreate) -> BuildResponse:
    """
    Create a new build.

    Can accept:
    - GW2Skill URL to parse
    - Custom requirements for AI to generate
    """
    try:
        logger.info(f"Creating build: {request.profession} - {request.role} - {request.game_mode}")
        response = await build_service.create_build(request)
        return response
    except Exception as e:
        logger.error(f"Error creating build: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating build: {str(e)}")


@router.get("/builds/{build_id}", response_model=Build)
async def get_build(build_id: str) -> Build:
    """Get a specific build by ID."""
    try:
        build = await build_service.get_build(build_id)
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")
        return build
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching build: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching build: {str(e)}")


@router.get("/builds", response_model=List[Build])
async def list_builds(
    profession: Optional[Profession] = Query(None),
    game_mode: Optional[GameMode] = Query(None),
    role: Optional[Role] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> List[Build]:
    """
    List builds with optional filters.
    """
    try:
        builds = await build_service.list_builds(
            profession=profession,
            game_mode=game_mode,
            role=role,
            limit=limit,
        )
        return builds
    except Exception as e:
        logger.error(f"Error listing builds: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing builds: {str(e)}")


@router.post("/builds/parse")
async def parse_gw2skill_url(url: str) -> BuildResponse:
    """
    Parse a GW2Skill URL and extract build information.
    """
    try:
        logger.info(f"Parsing GW2Skill URL: {url}")
        response = await build_service.parse_gw2skill_url(url)
        return response
    except Exception as e:
        logger.error(f"Error parsing URL: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing URL: {str(e)}")
