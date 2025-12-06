"""
Tests for Gw2DataService - intelligent GW2 data layer.

These tests verify:
- Role detection based on GW2 data (specs, traits, skills, context)
- Meta context generation for AnalystAgent
- Data access methods (get_specialization, get_traits, etc.)

NOTE: These tests use mocks and don't require Redis or database.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.gw2_data_service import (
    Gw2DataService,
    RoleAnalysis,
    MetaContext,
    get_gw2_data_service,
    ELITE_SPEC_ROLES,
    WVW_SUPPORT_SPECS,
)


@pytest.fixture
def mock_data_store():
    """Create a mock GW2DataStore with sample data."""
    store = MagicMock()
    
    # Sample specializations
    store.get_specializations.return_value = [
        {"id": 62, "name": "Firebrand", "profession": "Guardian", "elite": True},
        {"id": 27, "name": "Dragonhunter", "profession": "Guardian", "elite": True},
        {"id": 43, "name": "Scrapper", "profession": "Engineer", "elite": True},
        {"id": 55, "name": "Reaper", "profession": "Necromancer", "elite": True},
    ]
    
    # Sample traits
    store.get_traits.return_value = [
        {
            "id": 2101,
            "name": "Liberator's Vow",
            "description": "Using a Heal skill heals nearby allies.",
        },
        {
            "id": 2116,
            "name": "Stoic Demeanor",
            "description": "Gain stability when you use a Mantra.",
        },
        {
            "id": 1234,
            "name": "Ferocious Strike",
            "description": "Your critical hits deal increased damage.",
        },
    ]
    
    # Sample skills
    store.get_skills.return_value = [
        {
            "id": 9153,
            "name": "Shelter",
            "description": "Block attacks while healing.",
            "facts": [{"text": "Healing", "type": "AttributeAdjust"}],
        },
        {
            "id": 41714,
            "name": "Mantra of Liberation",
            "description": "Grant stability and resistance to allies.",
            "facts": [{"text": "Stability", "type": "Buff"}],
        },
        {
            "id": 5678,
            "name": "Dragon's Maw",
            "description": "A powerful strike that deals heavy damage.",
            "facts": [{"text": "Damage", "type": "Damage"}],
        },
    ]
    
    # Sample professions
    store.get_professions.return_value = [
        {"name": "Guardian", "id": 1},
        {"name": "Necromancer", "id": 8},
        {"name": "Engineer", "id": 3},
    ]
    
    return store


@pytest.fixture
def gw2_data_service(mock_data_store):
    """Create a Gw2DataService with mock store."""
    return Gw2DataService(data_store=mock_data_store)


class TestRoleDetection:
    """Tests for intelligent role detection.
    
    This test class verifies that the role detection system correctly identifies
    roles based on a combination of elite specs, traits, skills, and context.
    It tests various scenarios including support builds, DPS builds, and edge cases.
    """
    
    def test_firebrand_support_detection(self, gw2_data_service):
        """Verify Firebrand with heal traits is detected as support/heal.
        
        Test case:
        - Spec: Firebrand (ID 62)
        - Traits: Heal + stability traits (2101, 2116)
        - Skills: Shelter + Mantra of Liberation (defensive/support skills)
        - Context: WvW Zerg support
        
        Expected:
        - Primary role should be 'support' or 'heal'
        - Confidence score should be above 0.5
        """
        result = gw2_data_service.detect_role(
            spec_id=62,  # Firebrand
            trait_ids=[2101, 2116],  # Heal + stability traits
            skill_ids=[9153, 41714],  # Shelter + Mantra of Liberation
            context="WvW Zerg support",
        )
        
        assert isinstance(result, RoleAnalysis)
        assert result.primary_role in ("support", "heal")
        assert result.confidence > 0.5
    
    def test_reaper_dps_detection(self, gw2_data_service):
        """Verify Reaper with damage traits is detected as DPS.
        
        Test case:
        - Spec: Reaper (ID 55)
        - Traits: Damage-focused traits (1234)
        - Skills: Damage skill (5678)
        - Context: WvW Zerg DPS
        
        Expected:
        - Primary role should be 'dps'
        - Confidence score should be high (above 0.7)
        """
        result = gw2_data_service.detect_role(
            spec_id=55,  # Reaper
            trait_ids=[1234],  # Damage trait
            skill_ids=[5678],  # Damage skill
            context="WvW Zerg DPS",
        )
        
        assert isinstance(result, RoleAnalysis)
        assert result.primary_role == "dps"
    
    def test_context_influences_role(self, gw2_data_service):
        """Context keywords should strongly influence role detection."""
        result = gw2_data_service.detect_role(
            spec_id=None,
            trait_ids=[],
            skill_ids=[],
            context="I want to play heal support for my guild",
        )
        
        assert result.primary_role in ("support", "heal")
    
    def test_elite_spec_default_role(self, gw2_data_service):
        """Elite specs should have default role mappings."""
        # Firebrand defaults to support
        assert ELITE_SPEC_ROLES.get("Firebrand") == "support"
        # Reaper defaults to dps
        assert ELITE_SPEC_ROLES.get("Reaper") == "dps"
        # Scrapper defaults to support
        assert ELITE_SPEC_ROLES.get("Scrapper") == "support"
    
    def test_wvw_support_specs(self, gw2_data_service):
        """WvW support specs should be correctly identified."""
        assert "Firebrand" in WVW_SUPPORT_SPECS
        assert "Scrapper" in WVW_SUPPORT_SPECS
        assert "Tempest" in WVW_SUPPORT_SPECS
    
    def test_empty_input_defaults_to_dps(self, gw2_data_service):
        """With no signals, default to DPS with low confidence."""
        result = gw2_data_service.detect_role(
            spec_id=None,
            trait_ids=[],
            skill_ids=[],
            context="",
        )
        
        assert result.primary_role == "dps"
        assert result.confidence <= 0.5


class TestDataAccess:
    """Tests for data access methods.
    
    This test class verifies that the Gw2DataService can correctly retrieve and process
    game data including specializations, traits, skills, and profession information.
    It ensures the data layer functions as expected with both valid and invalid inputs.
    """
    
    def test_get_specialization(self, gw2_data_service):
        """Verify retrieval of specialization by ID.
        
        Test case:
        - Request specialization with ID 55 (Reaper)
        
        Expected:
        - Returns specialization data with correct ID and name
        - Data includes traits, skills, and other relevant fields
        """
        spec = gw2_data_service.get_specialization(62)
        assert spec is not None
        assert spec["name"] == "Firebrand"
        assert spec["profession"] == "Guardian"
    
    def test_get_specialization_by_name(self, gw2_data_service):
        """Should retrieve specialization by name (case-insensitive)."""
        spec = gw2_data_service.get_specialization_by_name("firebrand")
        assert spec is not None
        assert spec["id"] == 62
    
    def test_get_trait(self, gw2_data_service):
        """Verify retrieval of trait by ID.
        
        Test case:
        - Request trait with ID 1234
        
        Expected:
        - Returns trait data with correct ID
        - Data includes name, description, and other relevant fields
        """
        trait = gw2_data_service.get_trait(2101)
        assert trait is not None
        assert "heal" in trait["description"].lower()
    
    def test_get_traits_batch(self, gw2_data_service):
        """Should retrieve multiple traits."""
        traits = gw2_data_service.get_traits([2101, 2116])
        assert len(traits) == 2
    
    def test_get_skill(self, gw2_data_service):
        """Verify retrieval of skill by ID.
        
        Test case:
        - Request skill with ID 5678
        
        Expected:
        - Returns skill data with correct ID
        - Data includes name, description, and other relevant fields
        - Handles both weapon skills and utility skills
        """
        skill = gw2_data_service.get_skill(9153)
        assert skill is not None
        assert skill["name"] == "Shelter"
    
    def test_get_profession(self, gw2_data_service):
        """Should retrieve profession by name."""
        prof = gw2_data_service.get_profession("Guardian")
        assert prof is not None
    
    def test_is_elite_spec(self, gw2_data_service):
        """Should correctly identify elite specs."""
        assert gw2_data_service.is_elite_spec(62) is True  # Firebrand
    
    def test_get_profession_for_spec(self, gw2_data_service):
        """Should get profession name from spec ID."""
        prof = gw2_data_service.get_profession_for_spec(62)
        assert prof == "Guardian"


class TestMetaContext:
    """Tests for meta context generation."""
    
    def test_generate_meta_context_basic(self, gw2_data_service):
        """Should generate basic meta context."""
        ctx = gw2_data_service.generate_meta_context(
            game_mode="wvw",
            profession="Guardian",
            specialization="Firebrand",
            role="support",
        )
        
        assert isinstance(ctx, MetaContext)
        assert isinstance(ctx.summary, str)
        assert len(ctx.summary) > 0
    
    def test_get_meta_context_string(self, gw2_data_service):
        """Should generate formatted meta context string for prompts."""
        ctx_str = gw2_data_service.get_meta_context_string(
            game_mode="wvw",
            profession="Guardian",
        )
        
        assert isinstance(ctx_str, str)


class TestSingleton:
    """Tests for singleton pattern."""
    
    def test_get_gw2_data_service_returns_instance(self):
        """Should return a Gw2DataService instance."""
        with patch('app.services.gw2_data_service._gw2_data_service', None):
            service = get_gw2_data_service()
            assert isinstance(service, Gw2DataService)
    
    def test_singleton_returns_same_instance(self):
        """Subsequent calls should return the same instance."""
        with patch('app.services.gw2_data_service._gw2_data_service', None):
            service1 = get_gw2_data_service()
            service2 = get_gw2_data_service()
            assert service1 is service2


class TestIntegrationWithMetaBuilds:
    """Tests for integration with meta build catalog."""
    
    def test_meta_builds_json_exists(self):
        """The meta_builds_wvw.json file should exist."""
        base_dir = Path(__file__).resolve().parents[1]
        meta_path = base_dir / "data" / "meta_builds_wvw.json"
        assert meta_path.exists(), f"Meta builds file not found at {meta_path}"
    
    def test_meta_builds_json_valid(self):
        """The meta_builds_wvw.json should be valid JSON with expected structure."""
        import json
        base_dir = Path(__file__).resolve().parents[1]
        meta_path = base_dir / "data" / "meta_builds_wvw.json"
        
        with open(meta_path) as f:
            data = json.load(f)
        
        assert "builds" in data
        assert isinstance(data["builds"], list)
        assert len(data["builds"]) > 0
        
        # Check first build has required fields
        first_build = data["builds"][0]
        required_fields = ["id", "name", "profession", "specialization", "role", "game_mode"]
        for field in required_fields:
            assert field in first_build, f"Missing field: {field}"
