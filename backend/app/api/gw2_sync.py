"""GW2 data synchronization API endpoints."""

from fastapi import APIRouter

from app.api.endpoints import gw2_sync as endpoints
from app.core.config import settings

router = APIRouter()
router.include_router(
    endpoints.router,
    prefix="",  # The prefix is already included in the main router
    tags=["GW2 Data Sync"],
)
