"""API endpoints for GW2 data synchronization."""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.background import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.logging import logger
from app.db.session import get_db
from app.schemas.gw2_sync import SyncStatus, SyncTask
from app.services.gw2_sync_service import sync_gw2_data
from app.tasks.scheduler import scheduler, SYNC_JOB_ID

router = APIRouter()

# In-memory storage for sync status (in production, use a proper task queue like Celery or RQ)
_sync_status: Dict[str, Any] = {
    "is_running": False,
    "last_run": None,
    "last_success": None,
    "error": None,
}


@router.get("/status", response_model=SyncStatus)
async def get_sync_status() -> SyncStatus:
    """Get the current status of the GW2 data synchronization."""
    next_run = None
    job = scheduler.get_job(SYNC_JOB_ID)
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()
    
    return SyncStatus(
        is_running=_sync_status["is_running"],
        last_run=_sync_status["last_run"],
        last_success=_sync_status["last_success"],
        next_run=next_run,
        error=_sync_status["error"],
    )


@router.post("/trigger", response_model=SyncTask, status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> SyncTask:
    """
    Trigger a manual synchronization of GW2 data.
    
    This endpoint is only accessible to superusers.
    """
    if _sync_status["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Synchronization is already in progress",
        )
    
    # Update status
    _sync_status.update({
        "is_running": True,
        "last_run": datetime.utcnow().isoformat(),
        "error": None,
    })
    
    # Run the sync in the background
    background_tasks.add_task(run_sync, db)
    
    return SyncTask(
        message="Synchronization started",
        task_id="manual_sync",
        status="started",
    )


async def run_sync(db: AsyncSession):
    """Run the synchronization and update the status."""
    try:
        logger.info("Starting manual GW2 data synchronization...")
        await sync_gw2_data(db)
        _sync_status.update({
            "is_running": False,
            "last_success": datetime.utcnow().isoformat(),
            "error": None,
        })
        logger.info("Manual GW2 data synchronization completed successfully")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error during manual GW2 data synchronization: {error_msg}")
        _sync_status.update({
            "is_running": False,
            "error": error_msg,
        })
