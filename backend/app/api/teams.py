"""Team API router delegating to database-backed endpoints."""

from fastapi import APIRouter

from app.api.teams_db import router as teams_db_router

router = APIRouter()
router.include_router(teams_db_router, prefix="/teams", tags=["Teams"])


@router.get("/teams/legacy", include_in_schema=False)
async def legacy_notice() -> dict[str, str]:
    """Provide guidance for legacy clients when accessing deprecated endpoints."""
    return {"detail": "Legacy team endpoints have moved to database-backed routes."}
