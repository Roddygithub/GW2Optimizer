"""Security tests for DataCollector."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.models.build import Build, GameMode, Profession, Role
from app.models.learning import DataSource, TrainingDatapoint
from app.services.learning.data_collector import DataCollector
from datetime import datetime
import uuid

@pytest.mark.asyncio
async def test_path_traversal_protection():
    """Test that path traversal attempts are blocked."""
    collector = DataCollector()
    malicious_id = "../../etc/passwd"
    
    # Test load_datapoint with path traversal
    result = await collector.load_datapoint(malicious_id)
    assert result is None, "Path traversal in load_datapoint should be blocked"
    
    # Verify no file was created outside the storage directory
    assert not (Path("/etc/passwd").exists() and open("/etc/passwd").read().startswith("{")), \
        "Path traversal attack successful!"

@pytest.mark.asyncio
async def test_malicious_build_data():
    """Test handling of potentially malicious build data."""
    collector = DataCollector()
    
    # Create a build with potentially dangerous data
    malicious_build = Build(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name="<script>alert('xss')</script>",
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
    
    # This should not raise an exception
    datapoint = await collector.collect_build(malicious_build)
    assert datapoint is not None
    
    # The name should be properly escaped/sanitized
    loaded = await collector.load_datapoint(datapoint.id)
    assert loaded is not None
    assert "<script>" not in loaded.data.get("name", ""), "XSS injection possible!"

@pytest.mark.asyncio
async def test_file_permissions():
    """Test that files are created with secure permissions."""
    collector = DataCollector()
    
    # Create a test build
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
    
    # Check file permissions
    data_file = Path(collector.storage_path) / f"{datapoint.id}.bin"
    assert data_file.exists(), "Data file not created"
    
    # Check that the file is not world-writable
    file_mode = data_file.stat().st_mode
    assert not (file_mode & 0o002), "File is world-writable!"
    assert not (file_mode & 0o020), "File is group-writable!"

@pytest.mark.asyncio
async def test_large_input_protection():
    """Test protection against large input attacks."""
    from app.models.build import Profession, GameMode, Role
    
    collector = DataCollector()
    
    # Create a large data dictionary with a very large field
    large_data = {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "name": "Large Build",
        "profession": "Guardian",
        "game_mode": "zerg",
        "role": "healer",
        "specialization": "firebrand",
        "trait_lines": [],
        "skills": [],
        "equipment": [],
        "synergies": [],
        "counters": [],
        # Add a very large field that will make the data too big when serialized
        "large_field": "x" * (2 * 1024 * 1024)  # 2MB of data
    }
    
    # This should be rejected by _validate_data_size
    assert not collector._validate_data_size(large_data), \
        "Large data should be rejected by size validation"
