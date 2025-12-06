"""Integration tests for DataCollector with other services."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.models.build import Build, GameMode, Profession, Role
from app.models.learning import DataSource, TrainingDatapoint
from app.services.learning.data_collector import DataCollector
from app.services.build_service import BuildService
from datetime import datetime, timedelta
import json
import uuid

@pytest.fixture
def sample_build():
    """Create a sample build for testing."""
    return Build(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name="Test Firebrand",
        profession=Profession.GUARDIAN,
        game_mode=GameMode.ZERG,
        role=Role.HEALER,
        specialization="Firebrand",
        trait_lines=[],
        skills=[],
        equipment=[],
        synergies=[],
        counters=[]
    )

@pytest.fixture
def build_service(sample_build):
    """Create a mock build service."""
    service = AsyncMock()
    service.get_build.return_value = sample_build
    return service

@pytest.mark.asyncio
async def test_integration_with_build_service(build_service, sample_build):
    """Test DataCollector integration with BuildService."""
    # Setup
    collector = DataCollector()
    build_id = sample_build.id
    
    # Mock build service to return our sample build
    with patch('app.services.build_service.BuildService', return_value=build_service):
        # Test collecting a build by ID
        datapoint = await collector.collect_build(sample_build)
        
        # Verify the datapoint was created correctly
        assert datapoint is not None
        assert datapoint.build_id == build_id
        assert datapoint.game_mode == sample_build.game_mode
        assert datapoint.profession == sample_build.profession
        assert datapoint.role == sample_build.role
        assert datapoint.source == DataSource.AI_GENERATED
        
        # Verify the build data was stored
        loaded = await collector.load_datapoint(datapoint.id)
        assert loaded is not None
        assert loaded.data["id"] == build_id

@pytest.mark.asyncio
async def test_data_persistence(sample_build):
    """Test that data persists between DataCollector instances."""
    # First instance - collect data
    collector1 = DataCollector()
    datapoint = await collector1.collect_build(sample_build)
    
    # Create a new instance to simulate a new process
    collector2 = DataCollector()
    loaded = await collector2.load_datapoint(datapoint.id)
    
    # Verify data was persisted
    assert loaded is not None
    assert loaded.id == datapoint.id
    assert loaded.build_id == sample_build.id

@pytest.mark.asyncio
async def test_compression_efficiency(sample_build):
    """Test that data compression is working efficiently."""
    collector = DataCollector()
    datapoint = await collector.collect_build(sample_build)
    
    # Get the compressed file size
    data_file = Path(collector.storage_path) / f"{datapoint.id}.bin"
    compressed_size = data_file.stat().st_size
    
    # Estimate original size (JSON dump of the build)
    original_size = len(json.dumps(sample_build.model_dump(mode="json")))
    
    # Compression should reduce size (at least 20% smaller)
    assert compressed_size < original_size * 0.8
