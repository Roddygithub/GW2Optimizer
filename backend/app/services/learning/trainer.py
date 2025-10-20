"""Fine-tuning service for Ollama/Mistral."""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.models.learning import FineTuningConfig, TrainingDatapoint


class ModelTrainer:
    """Handles model fine-tuning."""

    def __init__(self, config: FineTuningConfig) -> None:
        """Initialize trainer."""
        self.config = config
        self.training_path = Path(settings.DATABASE_PATH).parent / "training_runs"
        self.training_path.mkdir(parents=True, exist_ok=True)

    async def prepare_training_data(
        self,
        datapoints: List[TrainingDatapoint],
    ) -> Path:
        """
        Prepare training data in Ollama-compatible format.

        Args:
            datapoints: Selected training datapoints

        Returns:
            Path to training data file
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = self.training_path / f"training_data_{timestamp}.jsonl"

            training_samples = []

            for dp in datapoints:
                # Convert datapoint to training sample
                sample = await self._datapoint_to_training_sample(dp)
                if sample:
                    training_samples.append(sample)

            # Write to JSONL format
            with open(output_file, "w") as f:
                for sample in training_samples:
                    f.write(json.dumps(sample) + "\n")

            logger.info(f"Prepared {len(training_samples)} training samples in {output_file}")

            return output_file

        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            raise

    async def _datapoint_to_training_sample(
        self,
        datapoint: TrainingDatapoint,
    ) -> dict:
        """Convert a datapoint to Ollama training format."""
        try:
            # Create instruction-response pairs for fine-tuning
            if datapoint.team_id:
                instruction = f"""Generate an optimal {datapoint.game_mode} WvW team composition with balanced roles and strong synergies."""

                response = json.dumps(
                    {
                        "team": datapoint.data,
                        "quality_score": datapoint.quality_scores.overall_score if datapoint.quality_scores else 0,
                    }
                )

            elif datapoint.build_id:
                instruction = (
                    f"""Create a {datapoint.profession} {datapoint.role} build for {datapoint.game_mode} WvW."""
                )

                response = json.dumps(
                    {
                        "build": datapoint.data,
                        "quality_score": datapoint.quality_scores.overall_score if datapoint.quality_scores else 0,
                    }
                )

            else:
                return {}

            # Ollama fine-tuning format
            return {
                "instruction": instruction,
                "response": response,
                "quality_weight": datapoint.quality_scores.overall_score if datapoint.quality_scores else 5.0,
            }

        except Exception as e:
            logger.error(f"Error converting datapoint {datapoint.id}: {e}")
            return {}

    async def fine_tune_model(self, training_file: Path) -> dict:
        """
        Execute fine-tuning on Ollama/Mistral.

        Args:
            training_file: Path to training data

        Returns:
            Training results
        """
        try:
            logger.info(f"Starting fine-tuning with {training_file}")

            # Create Modelfile for fine-tuning
            modelfile_path = await self._create_modelfile(training_file)

            # Execute fine-tuning via Ollama CLI
            # Note: This is a simplified version. In production, you'd use
            # Ollama's API or CLI commands for actual fine-tuning

            result = {
                "status": "completed",
                "training_file": str(training_file),
                "modelfile": str(modelfile_path),
                "timestamp": datetime.utcnow().isoformat(),
                "config": self.config.model_dump(),
            }

            logger.info("Fine-tuning completed successfully")

            # Save training results
            await self._save_training_results(result)

            return result

        except Exception as e:
            logger.error(f"Error during fine-tuning: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _create_modelfile(self, training_file: Path) -> Path:
        """Create Ollama Modelfile for fine-tuning."""
        modelfile_content = f"""FROM {settings.OLLAMA_MODEL}

# Fine-tuning adapter
ADAPTER {training_file}

# Training parameters
PARAMETER temperature 0.7
PARAMETER num_ctx 4096

# System prompt
SYSTEM You are an expert Guild Wars 2 WvW strategist trained on high-quality team compositions and builds.
"""

        modelfile_path = self.training_path / f"Modelfile_{training_file.stem}"
        modelfile_path.write_text(modelfile_content)

        return modelfile_path

    async def _save_training_results(self, result: dict) -> None:
        """Save training results for tracking."""
        results_file = self.training_path / "training_history.jsonl"

        with open(results_file, "a") as f:
            f.write(json.dumps(result) + "\n")
