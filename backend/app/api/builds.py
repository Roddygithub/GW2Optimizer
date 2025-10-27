"""Build API router delegating to database-backed endpoints."""

from fastapi import APIRouter

from app.api.builds_db import router as builds_db_router

router = APIRouter()
router.include_router(builds_db_router, prefix="/builds", tags=["Builds"])


@router.get("/builds/legacy", include_in_schema=False)
async def legacy_notice() -> dict[str, str]:
    """Provide guidance for legacy clients when accessing deprecated endpoints."""
    return {"detail": "Legacy build endpoints have moved to database-backed routes."}
