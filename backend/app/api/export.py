"""Export API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.builds_db import build_db_to_pydantic
from app.api.teams_db import team_db_to_pydantic
from app.core.logging import logger
from app.core.security import get_current_user_optional
from app.db.base import get_db
from app.db.models import UserDB
from app.models.build import BuildDB
from app.models.team import TeamCompositionDB
from app.services.exporter.snowcrows_exporter import SnowcrowsExporter

router = APIRouter()
exporter = SnowcrowsExporter()


@router.get("/export/build/{build_id}/json")
async def export_build_json(
    build_id: str,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Export build as Snowcrows JSON."""
    try:
        stmt = select(BuildDB).where(BuildDB.id == build_id)
        result = await db.execute(stmt)
        build_db = result.scalar_one_or_none()

        if not build_db:
            raise HTTPException(status_code=404, detail="Build not found")

        if not build_db.is_public and (
            current_user is None or str(build_db.user_id) != str(current_user.id)
        ):
            raise HTTPException(status_code=404, detail="Build not found")

        build = build_db_to_pydantic(build_db)

        exported = exporter.export_build_json(build)
        return JSONResponse(content=exported)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting build JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.get("/export/build/{build_id}/html", response_class=HTMLResponse)
async def export_build_html(
    build_id: str,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Export build as Snowcrows HTML."""
    try:
        stmt = select(BuildDB).where(BuildDB.id == build_id)
        result = await db.execute(stmt)
        build_db = result.scalar_one_or_none()

        if not build_db:
            raise HTTPException(status_code=404, detail="Build not found")

        if not build_db.is_public and (
            current_user is None or str(build_db.user_id) != str(current_user.id)
        ):
            raise HTTPException(status_code=404, detail="Build not found")

        build = build_db_to_pydantic(build_db)

        html = exporter.export_build_html(build)
        return HTMLResponse(content=html)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting build HTML: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.get("/export/team/{team_id}/json")
async def export_team_json(
    team_id: str,
    current_user: Optional[UserDB] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Export team composition as JSON."""
    try:
        stmt = select(TeamCompositionDB).where(TeamCompositionDB.id == team_id)
        result = await db.execute(stmt)
        team_db = result.scalar_one_or_none()

        if not team_db:
            raise HTTPException(status_code=404, detail="Team not found")

        if not team_db.is_public and (
            current_user is None or str(team_db.user_id) != str(current_user.id)
        ):
            raise HTTPException(status_code=404, detail="Team not found")

        team = team_db_to_pydantic(team_db)

        exported = exporter.export_team_json(team)
        return JSONResponse(content=exported)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting team JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
