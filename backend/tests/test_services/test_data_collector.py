"""
Tests for the DataCollector service.

These tests verify the functionality of the DataCollector class which is responsible for
collecting and storing training data for the learning system.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from datetime import datetime
from app.models.build import Build, GameMode, Profession, Role, Skill, Equipment
from app.models.team import TeamSlot, TeamSynergy
from app.models.learning import DataSource, TrainingDatapoint
from app.models.team import TeamComposition
from app.services.learning.data_collector import DataCollector

# Sample test data
SAMPLE_BUILD = Build(
    id=str(uuid4()),
    user_id=str(uuid4()),
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    name="Test Firebrand",
    profession=Profession.GUARDIAN,
    game_mode=GameMode.ZERG,
    role=Role.HEALER,
    specialization="Firebrand",
    trait_lines=[],
    skills=[
        Skill(slot="Heal", id=123, name="Mantra of Solace"),
        Skill(slot="Utility1", id=456, name="Mantra of Potence"),
        Skill(slot="Elite", id=789, name="Mantra of Liberation")
    ],
    equipment=[
        Equipment(slot="Weapon1", id=1, name="Mace", stats="Minstrel"),
        Equipment(slot="Armor", id=2, name="Heavy Armor", stats="Minstrel")
    ],
    synergies=["Might", "Quickness", "Stability"],
    counters=["Corruption", "Strips"]
)

SAMPLE_TEAM = TeamComposition(
    id=str(uuid4()),
    user_id=str(uuid4()),
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    name="Test Team",
    game_mode=GameMode.ZERG,
    team_size=5,
    description="A test team composition",
    is_public=False,
    slots=[
        TeamSlot(
            id=str(uuid4()),
            slot_number=1,
            build=SAMPLE_BUILD,
            player_name="Test Player",
            priority=1
        )
    ],
    synergies=[
        TeamSynergy(
            synergy_type="Might Stacking",
            description="Multiple sources of might generation",
            involved_slots=[1],
            strength=8.5
        )
    ],
    weaknesses=["Vulnerable to boon strips"],
    strengths=["High sustain", "Strong boon uptime"],
    overall_rating=8.0
)

SAMPLE_TEAM_DICT = {
    "id": str(uuid4()),
    "user_id": str(uuid4()),
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "name": "Test Team from Dict",
    "game_mode": "zerg",
    "team_size": 5,
    "description": "A test team composition from dict",
    "is_public": False,
    "slots": [
        {
            "team_composition_id": str(uuid4()),
            "build_id": SAMPLE_BUILD.id,
            "slot_number": 1,
            "player_name": "Test Player",
            "priority": 1
        }
    ],
    "synergies": [
        {
            "synergy_type": "Might Stacking",
            "description": "Multiple sources of might generation",
            "involved_slots": [1],
            "strength": 8.5
        }
    ],
    "weaknesses": ["Vulnerable to boon strips"],
    "strengths": ["High sustain", "Strong boon uptime"],
    "overall_rating": 8.0
}

SAMPLE_META_BUILD = {
    "id": "meta_firebrand_1",
    "name": "Meta Firebrand",
    "profession": "Guardian",
    "specialization": "Firebrand",
    "role": "heal",
    "game_mode": "zerg",
    "traits": {"Zeal": 1, "Honor": 2, "Firebrand": 3},
    "skills": [123, 456, 789],
    "equipment": {"weapon": "Mace", "armor": "Minstrel"},
}


@pytest.fixture
def data_collector(tmp_path):
    """Fixture to create a DataCollector with a temporary storage path."""
    storage_path = tmp_path / "training_data"
    with patch("app.core.config.settings.DATABASE_PATH", str(tmp_path / "test_db.sqlite")):
        yield DataCollector(storage_path=storage_path)


@pytest.fixture
def sample_build():
    """Fixture providing a sample build for testing."""
    return SAMPLE_BUILD


@pytest.fixture
def sample_team():
    """Fixture providing a sample team for testing."""
    return SAMPLE_TEAM


@pytest.fixture
def sample_team_dict():
    """Fixture providing a sample team as a dictionary for testing."""
    return SAMPLE_TEAM_DICT


@pytest.fixture
def sample_meta_build():
    """Fixture providing a sample meta build for testing."""
    return SAMPLE_META_BUILD


class TestDataCollector:
    """Test suite for the DataCollector class."""

    @pytest.mark.asyncio
    async def test_collect_build(self, data_collector, sample_build):
        """Test collecting a build for training."""
        # Test with default source (AI_GENERATED)
        datapoint = await data_collector.collect_build(sample_build)
        
        # Verify the datapoint was created correctly
        assert datapoint is not None
        assert datapoint.build_id == sample_build.id
        assert datapoint.game_mode == sample_build.game_mode
        assert datapoint.profession == sample_build.profession
        assert datapoint.role == sample_build.role
        assert datapoint.source == DataSource.AI_GENERATED
        assert datapoint.data == sample_build.model_dump(mode="json")
        
        # Test with a different source
        datapoint = await data_collector.collect_build(sample_build, source=DataSource.USER_IMPORT)
        assert datapoint.source == DataSource.USER_IMPORT
    
    @pytest.mark.asyncio
    async def test_collect_team(self, data_collector, sample_team):
        """Test collecting a team composition for training."""
        datapoint = await data_collector.collect_team(sample_team)
        
        assert datapoint is not None
        assert datapoint.team_id == sample_team.id
        assert datapoint.game_mode == sample_team.game_mode
        assert datapoint.source == DataSource.AI_GENERATED
        assert datapoint.data == sample_team.model_dump(mode="json")
    
    @pytest.mark.asyncio
    async def test_collect_team_from_dict(self, data_collector, sample_team_dict):
        """Test collecting a team from a dictionary."""
        game_mode = sample_team_dict["game_mode"]
        datapoint = await data_collector.collect_team_from_dict(
            team_data=sample_team_dict,
            game_mode=game_mode,
            source=DataSource.USER_IMPORT
        )
        
        assert datapoint is not None
        assert datapoint.team_id == sample_team_dict["id"]
        assert datapoint.game_mode == game_mode
        assert datapoint.source == DataSource.USER_IMPORT
        assert datapoint.data == sample_team_dict
    
    @pytest.mark.asyncio
    async def test_collect_meta_build(self, data_collector, sample_meta_build):
        """Test collecting a meta build for training."""
        datapoint = await data_collector.collect_meta_build(sample_meta_build)
        
        assert datapoint is not None
        assert datapoint.build_id == sample_meta_build["id"]
        assert datapoint.game_mode == sample_meta_build["game_mode"]
        assert datapoint.profession == sample_meta_build["profession"]
        assert datapoint.role == sample_meta_build["role"]
        assert datapoint.source == DataSource.COMMUNITY_SCRAPE
        assert datapoint.data == sample_meta_build
    
    @pytest.mark.asyncio
    async def test_load_datapoint(self, data_collector, sample_build):
        """Test loading a datapoint by ID."""
        # First collect a datapoint
        created_dp = await data_collector.collect_build(sample_build)
        
        # Now try to load it
        loaded_dp = await data_collector.load_datapoint(created_dp.id)
        
        assert loaded_dp is not None
        assert loaded_dp.id == created_dp.id
        assert loaded_dp.build_id == created_dp.build_id
        assert loaded_dp.data == created_dp.data
    
    @pytest.mark.asyncio
    async def test_get_all_datapoints(self, data_collector, sample_build, sample_team):
        """Test retrieving all datapoints."""
        # Start with no datapoints
        datapoints = await data_collector.get_all_datapoints()
        assert len(datapoints) == 0
        
        # Add a build datapoint
        build_dp = await data_collector.collect_build(sample_build)
        
        # Add a team datapoint
        team_dp = await data_collector.collect_team(sample_team)
        
        # Get all datapoints
        datapoints = await data_collector.get_all_datapoints()
        
        # Should have 2 datapoints
        assert len(datapoints) == 2
        
        # Verify the datapoints are in the list (check by ID)
        datapoint_ids = {dp.id for dp in datapoints}
        assert build_dp.id in datapoint_ids
        assert team_dp.id in datapoint_ids
    
    @pytest.mark.asyncio
    async def test_data_compression(self, data_collector, sample_build):
        """Test that data is properly compressed and decompressed."""
        # Collect a datapoint
        datapoint = await data_collector.collect_build(sample_build)
        
        # Get the path to the compressed data file
        data_file = Path(data_collector.storage_path) / f"{datapoint.id}.bin"
        
        # Verify the compressed file exists and is smaller than the original data
        assert data_file.exists()
        
        # The compressed size should be stored in the datapoint
        assert datapoint.compressed_size_bytes > 0
        
        # The compressed data should be smaller than the original JSON
        original_json = json.dumps(sample_build.model_dump(mode="json")).encode("utf-8")
        assert datapoint.compressed_size_bytes < len(original_json)
        
        # Verify we can load the data back
        loaded_dp = await data_collector.load_datapoint(datapoint.id)
        assert loaded_dp is not None
        assert loaded_dp.data == sample_build.model_dump(mode="json")
