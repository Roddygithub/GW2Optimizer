"""Monitoring tests for DataCollector."""

import pytest
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time

from app.models.build import Build, Profession, GameMode, Role
from app.services.learning.data_collector import DataCollector

@pytest.mark.asyncio
async def test_collection_metrics(caplog):
    """Test that collection metrics are logged correctly."""
    collector = DataCollector()

    # Create a test build
    test_build = Build(
        id="test-build-123",
        user_id="test-user-123",
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

    logger_name = "app.services.learning.data_collector"

    # Collect the build and capture logs
    with caplog.at_level(logging.INFO, logger=logger_name):
        datapoint = await collector.collect_build(test_build)

    messages = [record.getMessage() for record in caplog.records]
    assert any("Collected build" in msg for msg in messages)

    # Ensure datapoint_id and compressed_size are present in log extras
    assert any(
        getattr(record, "datapoint_id", None) == datapoint.id
        for record in caplog.records
    )
    assert any(
        getattr(record, "compressed_size", None) == datapoint.compressed_size_bytes
        for record in caplog.records
    )

@pytest.mark.asyncio
async def test_cache_metrics(caplog):
    """Test that cache metrics are logged correctly."""
    collector = DataCollector()

    # Create a test build
    test_build = Build(
        id="test-build-456",
        user_id="test-user-123",
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

    logger_name = "app.services.learning.data_collector"

    # First load: populate cache (may be a miss)
    await collector.load_datapoint(datapoint.id)

    # Second load: should be a cache hit and emit a log
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=logger_name):
        await collector.load_datapoint(datapoint.id)

    messages = [record.getMessage() for record in caplog.records]
    assert any("Cache hit for datapoint" in msg for msg in messages)

    # Ensure datapoint_id and cache_hit flag are present
    assert any(
        getattr(record, "datapoint_id", None) == datapoint.id
        and getattr(record, "cache_hit", None) is True
        for record in caplog.records
    )

@pytest.mark.asyncio
async def test_performance_metrics():
    """Test that performance metrics are collected correctly."""
    collector = DataCollector()

    # Create a test build
    test_build = Build(
        id="test-build-789",
        user_id="test-user-123",
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

    # Test collection performance
    start_time = time.time()
    datapoint = await collector.collect_build(test_build)
    collection_time = time.time() - start_time

    datapoint_id = datapoint.id

    # First load: uncached (loads from disk)
    start_time = time.time()
    _ = await collector.load_datapoint(datapoint_id)
    uncached_load_time = time.time() - start_time

    # Second load: cached (uses in-memory data)
    start_time = time.time()
    _ = await collector.load_datapoint(datapoint_id)
    cached_load_time = time.time() - start_time

    # Verify performance characteristics
    assert collection_time < 1.0, "Collection is too slow"
    assert uncached_load_time < 0.5, "Uncached load is too slow"
    assert cached_load_time < 0.5, "Cached load is too slow"
    assert cached_load_time <= uncached_load_time, "Cached load should not be slower than uncached"

@pytest.mark.asyncio
async def test_error_handling_metrics(caplog):
    """Test that error metrics are logged correctly."""
    collector = DataCollector()

    logger_name = "app.services.learning.data_collector"

    # Test with invalid build data
    with caplog.at_level(logging.ERROR, logger=logger_name):
        with pytest.raises(ValueError):
            await collector.collect_build(None)

    messages = [record.getMessage() for record in caplog.records]
    assert any("Error collecting build" in msg for msg in messages)

    # Test with non-existent datapoint
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=logger_name):
        result = await collector.load_datapoint("non-existent-id")

    assert result is None
    messages = [record.getMessage() for record in caplog.records]
    assert any("Datapoint not found" in msg for msg in messages)
