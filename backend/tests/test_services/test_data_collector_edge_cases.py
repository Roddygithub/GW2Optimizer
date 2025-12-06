"""Edge case tests for DataCollector."""

import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import os

from app.models.build import Build, GameMode, Profession, Role
from app.models.learning import DataSource, TrainingDatapoint
from app.services.learning.data_collector import DataCollector
from datetime import datetime
import uuid

@pytest.mark.asyncio
async def test_collect_invalid_build():
    """Test collecting an invalid build."""
    from pydantic import ValidationError
    
    collector = DataCollector()
    
    # Create an invalid build (missing required fields)
    with pytest.raises(ValidationError):
        invalid_build = Build(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # Missing required fields like name, profession, etc.
        )

@pytest.mark.asyncio
async def test_load_nonexistent_datapoint():
    """Test loading a datapoint that doesn't exist."""
    collector = DataCollector()
    non_existent_id = "non-existent-id-123"
    
    datapoint = await collector.load_datapoint(non_existent_id)
    assert datapoint is None

@pytest.mark.asyncio
async def test_corrupted_data_file():
    """Test handling of corrupted data files."""
    import zlib
    
    collector = DataCollector()
    
    # Create a test datapoint
    test_build = Build(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name="Test Build",
        profession=Profession.GUARDIAN,
        game_mode=GameMode.ZERG,
        role=Role.HEALER,
        specialization="Test",
        trait_lines=[],
        skills=[],
        equipment=[],
        synergies=[],
        counters=[]
    )
    
    # Collect the build
    datapoint = await collector.collect_build(test_build)
    
    # Corrupt the data file
    data_file = Path(collector.storage_path) / f"{datapoint.id}.bin"
    with open(data_file, 'wb') as f:
        f.write(b'corrupted data')
    
    # Try to load the corrupted datapoint
    loaded = await collector.load_datapoint(datapoint.id)
    
    # The method should handle the error and return None
    assert loaded is None

@pytest.mark.asyncio
async def test_concurrent_access():
    """Test concurrent access to the data collector."""
    import asyncio
    
    collector = DataCollector()
    build_ids = [str(uuid.uuid4()) for _ in range(5)]
    
    async def collect_build_task(build_id):
        build = Build(
            id=build_id,
            user_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            name=f"Concurrent Build {build_id[:8]}",
            profession=Profession.GUARDIAN,
            game_mode=GameMode.ZERG,
            role=Role.HEALER,
            specialization="Test",
            trait_lines=[],
            skills=[],
            equipment=[],
            synergies=[],
            counters=[]
        )
        return await collector.collect_build(build)
    
    # Run multiple collection tasks concurrently
    tasks = [collect_build_task(build_id) for build_id in build_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all tasks completed successfully
    for result in results:
        assert isinstance(result, TrainingDatapoint)
    
    # Verify all datapoints were stored
    datapoints = await collector.get_all_datapoints()
    stored_ids = {dp.build_id for dp in datapoints if dp.build_id in build_ids}
    assert len(stored_ids) == len(build_ids)
