"""Learning system API endpoints."""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.logging import logger
from app.models.learning import FineTuningConfig, LearningStats, StorageConfig
from app.services.learning.pipeline import LearningPipeline

router = APIRouter()

# Initialize pipeline with default configs
pipeline = LearningPipeline(
    finetuning_config=FineTuningConfig(),
    storage_config=StorageConfig(),
)


@router.get("/stats", response_model=LearningStats)
async def get_learning_stats() -> LearningStats:
    """
    Get current learning system statistics.

    Returns:
    - Total datapoints collected
    - Quality distribution
    - Storage usage
    - Last training date
    """
    try:
        stats = await pipeline.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/pipeline/run")
async def run_pipeline(background_tasks: BackgroundTasks) -> dict:
    """
    Trigger the learning pipeline manually.

    The pipeline will run in the background and includes:
    1. Data evaluation
    2. Selection of high-quality data
    3. Fine-tuning (if conditions met)
    4. Storage cleanup

    Returns immediately with task ID.
    """
    try:
        # Run pipeline in background
        background_tasks.add_task(pipeline.run_full_pipeline)

        return {
            "status": "started",
            "message": "Learning pipeline triggered in background",
        }
    except Exception as e:
        logger.error(f"Error starting pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/config/finetuning", response_model=FineTuningConfig)
async def get_finetuning_config() -> FineTuningConfig:
    """Get current fine-tuning configuration."""
    return pipeline.finetuning_config


@router.post("/config/finetuning", response_model=FineTuningConfig)
async def update_finetuning_config(config: FineTuningConfig) -> FineTuningConfig:
    """Update fine-tuning configuration."""
    pipeline.finetuning_config = config
    pipeline.selector.config = config
    pipeline.trainer.config = config

    logger.info("Fine-tuning configuration updated")
    return config


@router.get("/config/storage", response_model=StorageConfig)
async def get_storage_config() -> StorageConfig:
    """Get current storage configuration."""
    return pipeline.storage_config


@router.post("/config/storage", response_model=StorageConfig)
async def update_storage_config(config: StorageConfig) -> StorageConfig:
    """Update storage configuration."""
    pipeline.storage_config = config
    pipeline.storage_manager.config = config

    logger.info("Storage configuration updated")
    return config


@router.post("/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks) -> dict:
    """
    Trigger storage cleanup manually.

    Cleans up:
    - Old datapoints
    - Low-quality data
    - Archived data past retention period
    """
    try:

        async def cleanup_task() -> None:
            datapoints = await pipeline.collector.get_all_datapoints()
            await pipeline.storage_manager.cleanup(datapoints)

        background_tasks.add_task(cleanup_task)

        return {
            "status": "started",
            "message": "Cleanup triggered in background",
        }
    except Exception as e:
        logger.error(f"Error triggering cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
