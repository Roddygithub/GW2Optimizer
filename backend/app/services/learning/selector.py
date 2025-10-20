"""Data selection service for training."""

from typing import List

from app.core.logging import logger
from app.models.learning import FineTuningConfig, TrainingDatapoint


class DataSelector:
    """Selects best quality datapoints for training."""

    def __init__(self, config: FineTuningConfig) -> None:
        """Initialize selector."""
        self.config = config

    async def select_training_data(
        self,
        datapoints: List[TrainingDatapoint],
    ) -> List[TrainingDatapoint]:
        """
        Select best datapoints for training.
        
        Args:
            datapoints: All available datapoints
            
        Returns:
            Selected high-quality datapoints
        """
        try:
            # Filter by validation status
            validated = [dp for dp in datapoints if dp.is_validated]
            
            # Filter by quality threshold
            high_quality = [
                dp for dp in validated
                if dp.quality_scores and
                dp.quality_scores.overall_score >= self.config.min_quality_threshold
            ]
            
            # Sort by quality (descending)
            high_quality.sort(
                key=lambda dp: dp.quality_scores.overall_score if dp.quality_scores else 0,
                reverse=True,
            )
            
            # Limit to max training samples
            selected = high_quality[:self.config.max_training_samples]
            
            logger.info(
                f"Selected {len(selected)} datapoints for training "
                f"(from {len(datapoints)} total, {len(validated)} validated)"
            )
            
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting training data: {e}")
            return []

    async def should_trigger_training(
        self,
        available_datapoints: int,
        last_training_days_ago: int,
    ) -> bool:
        """
        Determine if training should be triggered.
        
        Args:
            available_datapoints: Number of available high-quality datapoints
            last_training_days_ago: Days since last training
            
        Returns:
            True if training should be triggered
        """
        # Check minimum datapoints
        if available_datapoints < self.config.min_datapoints:
            logger.info(
                f"Not enough datapoints for training: "
                f"{available_datapoints} < {self.config.min_datapoints}"
            )
            return False
        
        # Check training interval
        if last_training_days_ago < self.config.training_interval_days:
            logger.info(
                f"Too soon since last training: "
                f"{last_training_days_ago} < {self.config.training_interval_days} days"
            )
            return False
        
        logger.info("Training conditions met!")
        return True
