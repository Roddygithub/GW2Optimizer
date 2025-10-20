"""Data collection service for learning system."""

import json
import uuid
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.build import Build
from app.models.learning import DataSource, TrainingDatapoint
from app.models.team import TeamComposition


class DataCollector:
    """Collects and stores training data."""

    def __init__(self) -> None:
        """Initialize data collector."""
        self.storage_path = Path(settings.DATABASE_PATH).parent / "training_data"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.datapoints_file = self.storage_path / "datapoints.jsonl"
        self.stats_file = self.storage_path / "stats.json"

    async def collect_build(
        self,
        build: Build,
        source: DataSource = DataSource.AI_GENERATED,
    ) -> TrainingDatapoint:
        """
        Collect a build for training.

        Args:
            build: Build to collect
            source: Source of the build

        Returns:
            Created training datapoint
        """
        try:
            # Convert build to dict
            build_data = build.model_dump(mode="json")

            # Compress data
            compressed_data = self._compress_data(build_data)

            # Create datapoint
            datapoint = TrainingDatapoint(
                id=str(uuid.uuid4()),
                build_id=build.id,
                data=build_data,
                game_mode=build.game_mode.value,
                profession=build.profession.value if build.profession else None,
                role=build.role.value if build.role else None,
                source=source,
                compressed_size_bytes=len(compressed_data),
            )

            # Store datapoint
            await self._store_datapoint(datapoint, compressed_data)

            logger.info(f"Collected build {build.id} from {source.value}")
            return datapoint

        except Exception as e:
            logger.error(f"Error collecting build: {e}")
            raise

    async def collect_team(
        self,
        team: TeamComposition,
        source: DataSource = DataSource.AI_GENERATED,
    ) -> TrainingDatapoint:
        """
        Collect a team composition for training.

        Args:
            team: Team to collect
            source: Source of the team

        Returns:
            Created training datapoint
        """
        try:
            team_data = team.model_dump(mode="json")
            compressed_data = self._compress_data(team_data)

            datapoint = TrainingDatapoint(
                id=str(uuid.uuid4()),
                team_id=team.id,
                data=team_data,
                game_mode=team.game_mode.value,
                source=source,
                compressed_size_bytes=len(compressed_data),
            )

            await self._store_datapoint(datapoint, compressed_data)

            logger.info(f"Collected team {team.id} from {source.value}")
            return datapoint

        except Exception as e:
            logger.error(f"Error collecting team: {e}")
            raise

    def _compress_data(self, data: Dict) -> bytes:
        """Compress data using zlib."""
        json_str = json.dumps(data, separators=(",", ":"))
        return zlib.compress(json_str.encode("utf-8"))

    def _decompress_data(self, compressed: bytes) -> Dict:
        """Decompress data."""
        json_str = zlib.decompress(compressed).decode("utf-8")
        return json.loads(json_str)

    async def _store_datapoint(
        self,
        datapoint: TrainingDatapoint,
        compressed_data: bytes,
    ) -> None:
        """Store datapoint to disk."""
        # Store metadata in JSONL file
        with open(self.datapoints_file, "a") as f:
            metadata = datapoint.model_dump(mode="json", exclude={"data"})
            f.write(json.dumps(metadata) + "\n")

        # Store compressed data separately
        data_file = self.storage_path / f"{datapoint.id}.bin"
        with open(data_file, "wb") as f:
            f.write(compressed_data)

    async def load_datapoint(self, datapoint_id: str) -> Optional[TrainingDatapoint]:
        """Load a datapoint by ID."""
        try:
            # Find metadata in JSONL
            with open(self.datapoints_file, "r") as f:
                for line in f:
                    metadata = json.loads(line.strip())
                    if metadata.get("id") == datapoint_id:
                        # Load compressed data
                        data_file = self.storage_path / f"{datapoint_id}.bin"
                        if data_file.exists():
                            with open(data_file, "rb") as df:
                                compressed = df.read()
                            data = self._decompress_data(compressed)
                            metadata["data"] = data

                        return TrainingDatapoint(**metadata)

            return None

        except Exception as e:
            logger.error(f"Error loading datapoint {datapoint_id}: {e}")
            return None

    async def get_all_datapoints(self) -> list[TrainingDatapoint]:
        """Load all datapoints (metadata only, without full data)."""
        datapoints = []

        try:
            if not self.datapoints_file.exists():
                return []

            with open(self.datapoints_file, "r") as f:
                for line in f:
                    if line.strip():
                        metadata = json.loads(line.strip())
                        datapoints.append(TrainingDatapoint(**metadata))

            return datapoints

        except Exception as e:
            logger.error(f"Error loading datapoints: {e}")
            return []
