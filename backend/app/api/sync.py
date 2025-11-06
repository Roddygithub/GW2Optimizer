"""Endpoints for triggering Guild Wars 2 synchronisation jobs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_current_user_optional
from app.db.session import get_db
from app.services.etl_gw2 import sync_all

router = APIRouter(tags=["Sync"])
# Le préfixe "/sync" est déjà défini dans main.py lors de l'inclusion du routeur


async def require_sync_access(user: Any = Depends(get_current_user_optional)) -> Any:
    """Ensure the caller is allowed to trigger the GW2 synchronisation."""

    if settings.GW2_SYNC_OPEN:
        return user

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if not getattr(user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")

    return user


@router.post("/gw2", status_code=status.HTTP_202_ACCEPTED)
async def trigger_gw2_sync(
    _: Any = Depends(require_sync_access),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger the GW2 data synchronisation pipeline."""

    try:
        result = await sync_all(session)
    except Exception:
        logger.exception("GW2 synchronisation failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GW2 synchronisation failed")

    logger.info("GW2 synchronisation triggered via API: %s", result)
    return {"status": "accepted", "result": result}
