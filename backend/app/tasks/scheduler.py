"""Background task scheduler for GW2 data synchronization."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from fastapi import Depends

from app.core.config import settings
from app.db.session import get_db
from app.services.gw2_sync_service import sync_gw2_data

logger = logging.getLogger(__name__)

# Job store and executors configuration
job_stores = {
    'default': SQLAlchemyJobStore(url=str(settings.DATABASE_URL).replace("+aiosqlite", ""))
}

executors = {
    'default': ThreadPoolExecutor(20),
}

job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 60 * 60,  # 1 hour
}

# Initialize the scheduler
scheduler = AsyncIOScheduler(
    jobstores=job_stores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="UTC"
)

# Store the sync job ID
SYNC_JOB_ID = "gw2_data_sync"


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance."""
    return scheduler


async def sync_job():
    """Background job to synchronize GW2 data."""
    logger.info("Starting scheduled GW2 data synchronization...")
    try:
        # Get a new DB session for this job
        async for db in get_db():
            await sync_gw2_data(db)
        logger.info("GW2 data synchronization completed successfully")
    except Exception as e:
        logger.error(f"Error during GW2 data synchronization: {e}")
        raise


def schedule_gw2_sync():
    """Schedule the GW2 data synchronization job."""
    # Remove existing job if it exists
    if scheduler.get_job(SYNC_JOB_ID):
        scheduler.remove_job(SYNC_JOB_ID)
    
    # Schedule the job to run every 12 hours
    scheduler.add_job(
        sync_job,
        'interval',
        hours=12,
        id=SYNC_JOB_ID,
        name="GW2 Data Synchronization",
        replace_existing=True,
        next_run_time=datetime.utcnow() + timedelta(seconds=30),  # Start 30 seconds after startup
    )
    logger.info("Scheduled GW2 data synchronization job")


def start_scheduler():
    """Start the scheduler if not already running."""
    if not scheduler.running:
        # Schedule the GW2 sync job
        schedule_gw2_sync()
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down")


# Register event handlers
async def startup_event():
    """Start the scheduler when the application starts."""
    start_scheduler()


async def shutdown_event():
    """Shutdown the scheduler when the application stops."""
    shutdown_scheduler()
