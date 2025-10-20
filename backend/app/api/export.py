"""Export API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

from app.core.logging import logger
from app.services.build_service import BuildService
from app.services.team_service import TeamService
from app.services.exporter.snowcrows_exporter import SnowcrowsExporter

router = APIRouter()
exporter = SnowcrowsExporter()


@router.get("/export/build/{build_id}/json")
async def export_build_json(build_id: str) -> JSONResponse:
    """Export build as Snowcrows JSON."""
    try:
        build_service = BuildService()
        build = await build_service.get_build(build_id)

        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        exported = exporter.export_build_json(build)
        return JSONResponse(content=exported)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting build JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.get("/export/build/{build_id}/html", response_class=HTMLResponse)
async def export_build_html(build_id: str) -> HTMLResponse:
    """Export build as Snowcrows HTML."""
    try:
        build_service = BuildService()
        build = await build_service.get_build(build_id)

        if not build:
            raise HTTPException(status_code=404, detail="Build not found")

        html = exporter.export_build_html(build)
        return HTMLResponse(content=html)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting build HTML: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.get("/export/team/{team_id}/json")
async def export_team_json(team_id: str) -> JSONResponse:
    """Export team composition as JSON."""
    try:
        team_service = TeamService()
        team = await team_service.get_team(team_id)

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        exported = exporter.export_team_json(team)
        return JSONResponse(content=exported)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting team JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
