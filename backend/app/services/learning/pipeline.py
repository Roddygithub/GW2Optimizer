"""Automatic learning pipeline orchestrator."""

from datetime import datetime
from pathlib import Path
from typing import Dict
import json

from app.core.logging import logger
from app.models.learning import DataSource, FineTuningConfig, LearningStats, StorageConfig
from app.services.learning.data_collector import DataCollector
from app.services.learning.evaluator import Evaluator
from app.services.learning.selector import DataSelector
from app.services.learning.storage_manager import StorageManager
from app.services.learning.trainer import ModelTrainer


class LearningPipeline:
    """Orchestrates the automatic learning pipeline."""

    def __init__(
        self,
        finetuning_config: FineTuningConfig,
        storage_config: StorageConfig,
    ) -> None:
        """Initialize pipeline."""
        self.collector = DataCollector()
        self.evaluator = Evaluator()
        self.selector = DataSelector(finetuning_config)
        self.storage_manager = StorageManager(storage_config)
        self.trainer = ModelTrainer(finetuning_config)

        self.finetuning_config = finetuning_config
        self.storage_config = storage_config

        self.last_training_date: datetime | None = None

    async def ingest_meta_builds(self) -> int:
        try:
            base_dir = Path(__file__).resolve().parents[3]
            json_path = base_dir / "data" / "learning" / "external" / "meta_builds_wvw.json"
            if not json_path.is_file():
                return 0
            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Failed to read meta builds file", extra={"error": str(e)})
                return 0
            items = payload.get("builds") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                return 0
            existing_datapoints = await self.collector.get_all_datapoints()
            existing_ids = {
                dp.build_id
                for dp in existing_datapoints
                if dp.build_id and dp.source == DataSource.COMMUNITY_SCRAPE
            }

            count = 0
            for meta in items:
                if not isinstance(meta, dict):
                    continue
                try:
                    build_id = str(meta.get("id")) if meta.get("id") is not None else None
                    if build_id and build_id in existing_ids:
                        continue
                    dp = await self.collector.collect_meta_build(meta)
                    if dp.build_id:
                        existing_ids.add(dp.build_id)
                    count += 1
                except Exception as e:
                    logger.error("Failed to collect meta build into training data", extra={"error": str(e)})
            return count
        except Exception as e:
            logger.error("Meta builds ingestion failed", extra={"error": str(e)})
            return 0

    async def run_full_pipeline(self) -> Dict:
        """
        Execute the complete learning pipeline.

        Pipeline stages:
        1. Load collected datapoints
        2. Evaluate unevaluated datapoints
        3. Select high-quality data for training
        4. Trigger fine-tuning if conditions met
        5. Cleanup old/low-quality data

        Returns:
            Pipeline execution statistics
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting Learning Pipeline Execution")
            logger.info("=" * 60)

            stats = {
                "pipeline_start": datetime.utcnow().isoformat(),
                "stages_completed": [],
            }

            # Stage 1: Load datapoints
            logger.info("Stage 1: Loading datapoints...")
            datapoints = await self.collector.get_all_datapoints()
            stats["total_datapoints"] = len(datapoints)
            stats["stages_completed"].append("load")

            # Stage 2: Evaluate unevaluated datapoints
            logger.info("Stage 2: Evaluating datapoints...")
            evaluation_stats = await self._evaluate_datapoints(datapoints)
            stats.update(evaluation_stats)
            stats["stages_completed"].append("evaluate")

            # Stage 3: Select training data
            logger.info("Stage 3: Selecting training data...")
            selected = await self.selector.select_training_data(datapoints)
            stats["selected_for_training"] = len(selected)
            stats["stages_completed"].append("select")

            # Stage 4: Fine-tuning (if conditions met)
            logger.info("Stage 4: Checking fine-tuning conditions...")
            days_since_training = self._days_since_last_training()
            should_train = await self.selector.should_trigger_training(
                len(selected),
                days_since_training,
            )

            if should_train:
                logger.info("Triggering fine-tuning...")
                training_result = await self._execute_training(selected)
                stats["training"] = training_result
                stats["stages_completed"].append("train")
            else:
                logger.info("Skipping training (conditions not met)")
                stats["training"] = {"status": "skipped"}

            # Stage 5: Cleanup
            logger.info("Stage 5: Storage cleanup...")
            cleanup_stats = await self.storage_manager.cleanup(datapoints)
            stats["cleanup"] = cleanup_stats
            stats["stages_completed"].append("cleanup")

            stats["pipeline_end"] = datetime.utcnow().isoformat()
            stats["status"] = "completed"

            logger.info("=" * 60)
            logger.info("Pipeline Execution Completed Successfully")
            logger.info(f"Stages: {' -> '.join(stats['stages_completed'])}")
            logger.info("=" * 60)

            return stats

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "pipeline_end": datetime.utcnow().isoformat(),
            }

    async def _evaluate_datapoints(self, datapoints: list) -> Dict:
        """Evaluate all unevaluated datapoints."""
        evaluated = 0
        total_score = 0.0

        for dp in datapoints:
            if not dp.is_validated or not dp.quality_scores:
                try:
                    quality = await self.evaluator.evaluate_datapoint(dp)
                    dp.quality_scores = quality
                    await self.evaluator.mark_validated(dp)

                    evaluated += 1
                    total_score += quality.overall_score

                except Exception as e:
                    logger.error(f"Failed to evaluate datapoint {dp.id}: {e}")

        avg_score = total_score / evaluated if evaluated > 0 else 0.0

        return {
            "datapoints_evaluated": evaluated,
            "average_quality_score": avg_score,
        }

    async def _execute_training(self, selected_datapoints: list) -> Dict:
        """Execute fine-tuning process."""
        try:
            # Prepare training data
            training_file = await self.trainer.prepare_training_data(selected_datapoints)

            # Fine-tune model
            result = await self.trainer.fine_tune_model(training_file)

            # Update last training date
            self.last_training_date = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Training execution failed: {e}")
            return {"status": "failed", "error": str(e)}

    def _days_since_last_training(self) -> int:
        """Calculate days since last training."""
        if not self.last_training_date:
            return 999  # Force training if never trained

        delta = datetime.utcnow() - self.last_training_date
        return delta.days

    async def get_stats(self) -> LearningStats:
        """Get current learning system statistics."""
        try:
            datapoints = await self.collector.get_all_datapoints()

            stats = LearningStats(
                total_datapoints=len(datapoints),
                validated_datapoints=sum(1 for dp in datapoints if dp.is_validated),
                archived_datapoints=sum(1 for dp in datapoints if dp.is_archived),
            )

            # Calculate quality distribution
            validated = [dp for dp in datapoints if dp.quality_scores]
            if validated:
                scores = [dp.quality_scores.overall_score for dp in validated]
                stats.average_quality_score = sum(scores) / len(scores)

                stats.high_quality_count = sum(1 for s in scores if s >= 8)
                stats.medium_quality_count = sum(1 for s in scores if 5 <= s < 8)
                stats.low_quality_count = sum(1 for s in scores if s < 5)

            # Storage size
            storage_size_gb = await self.storage_manager._get_storage_size_gb()
            stats.total_storage_bytes = int(storage_size_gb * 1024**3)

            # By source
            for dp in datapoints:
                source = dp.source.value
                stats.datapoints_by_source[source] = stats.datapoints_by_source.get(source, 0) + 1

            stats.last_training_date = self.last_training_date

            return stats

        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return LearningStats()
