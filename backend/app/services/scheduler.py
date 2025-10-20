"""Automatic scheduler for learning pipeline."""

import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import logger
from app.models.learning import FineTuningConfig, StorageConfig
from app.services.learning.pipeline import LearningPipeline


class PipelineScheduler:
    """Scheduler for automatic learning pipeline execution."""

    def __init__(self) -> None:
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.pipeline = LearningPipeline(
            finetuning_config=FineTuningConfig(),
            storage_config=StorageConfig(),
        )

    async def run_pipeline_task(self) -> None:
        """Task to run the learning pipeline."""
        try:
            logger.info("Scheduled pipeline execution starting...")
            stats = await self.pipeline.run_full_pipeline()
            logger.info(f"Scheduled pipeline completed: {stats.get('status')}")
        except Exception as e:
            logger.error(f"Scheduled pipeline failed: {e}")

    def start(self) -> None:
        """Start the scheduler."""
        # Run pipeline daily at 3 AM
        self.scheduler.add_job(
            self.run_pipeline_task,
            CronTrigger(hour=3, minute=0),
            id="learning_pipeline",
            name="Learning Pipeline Execution",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Pipeline scheduler started (daily at 3:00 AM)")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Pipeline scheduler stopped")


# Global scheduler instance
scheduler = PipelineScheduler()
