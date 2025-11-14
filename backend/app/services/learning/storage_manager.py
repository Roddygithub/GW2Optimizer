"""Storage management for automatic cleanup."""

from datetime import datetime
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.models.learning import StorageConfig, TrainingDatapoint


class StorageManager:
    """Manages storage and automatic cleanup."""

    def __init__(self, config: StorageConfig) -> None:
        """Initialize storage manager."""
        self.config = config
        self.storage_path = Path(settings.DATABASE_PATH).parent / "training_data"

    async def cleanup(self, datapoints: List[TrainingDatapoint]) -> dict:
        """
        Perform automatic cleanup.

        Args:
            datapoints: All datapoints

        Returns:
            Cleanup statistics
        """
        try:
            stats = {
                "archived": 0,
                "deleted": 0,
                "bytes_freed": 0,
            }

            current_size_gb = await self._get_storage_size_gb()
            logger.info(f"Current storage: {current_size_gb:.2f} GB")

            # Check if cleanup is needed
            if current_size_gb < self.config.max_storage_gb * 0.9:
                logger.info("Storage usage OK, no cleanup needed")
                return stats

            now = datetime.utcnow()

            for dp in datapoints:
                age_days = (now - dp.timestamp).days

                # Delete old low-quality datapoints
                if age_days > self.config.delete_threshold_days or (
                    dp.quality_scores and dp.quality_scores.overall_score < self.config.min_quality_to_keep
                ):

                    bytes_freed = await self._delete_datapoint(dp)
                    stats["deleted"] += 1
                    stats["bytes_freed"] += bytes_freed

                # Archive old datapoints
                elif age_days > self.config.archive_threshold_days and not dp.is_archived:

                    await self._archive_datapoint(dp)
                    stats["archived"] += 1

            logger.info(
                f"Cleanup complete: archived={stats['archived']}, "
                f"deleted={stats['deleted']}, freed={stats['bytes_freed'] / 1024 / 1024:.2f} MB"
            )

            return stats

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"archived": 0, "deleted": 0, "bytes_freed": 0}

    async def _get_storage_size_gb(self) -> float:
        """Get total storage size in GB."""
        try:
            total_size = 0
            for path in self.storage_path.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
            return total_size / (1024**3)
        except Exception as e:
            logger.error(f"Error calculating storage size: {e}")
            return 0.0

    async def _delete_datapoint(self, datapoint: TrainingDatapoint) -> int:
        """Delete a datapoint and return bytes freed."""
        try:
            data_file = self.storage_path / f"{datapoint.id}.bin"
            bytes_freed = 0

            if data_file.exists():
                bytes_freed = data_file.stat().st_size
                data_file.unlink()

            # Remove from JSONL (rebuild file without this entry)
            await self._remove_from_jsonl(datapoint.id)

            logger.debug(f"Deleted datapoint {datapoint.id}")
            return bytes_freed

        except Exception as e:
            logger.error(f"Error deleting datapoint {datapoint.id}: {e}")
            return 0

    async def _archive_datapoint(self, datapoint: TrainingDatapoint) -> None:
        """Archive a datapoint (compress further or move to cold storage)."""
        try:
            # For now, just mark as archived
            # In production, could move to cheaper storage
            datapoint.is_archived = True
            datapoint.archive_date = datetime.utcnow()

            logger.debug(f"Archived datapoint {datapoint.id}")

        except Exception as e:
            logger.error(f"Error archiving datapoint {datapoint.id}: {e}")

    async def _remove_from_jsonl(self, datapoint_id: str) -> None:
        """Remove entry from JSONL file."""
        try:
            import json

            jsonl_file = self.storage_path / "datapoints.jsonl"
            if not jsonl_file.exists():
                return

            # Read all lines except the one to delete
            lines = []
            with open(jsonl_file, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data.get("id") != datapoint_id:
                        lines.append(line)

            # Rewrite file
            with open(jsonl_file, "w") as f:
                f.writelines(lines)

        except Exception as e:
            logger.error(f"Error removing from JSONL: {e}")
