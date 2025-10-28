"""Tests for the GW2 sync service."""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gw2_sync_service import GW2SyncService, sync_gw2_data
from app.models.gw2.entities import Profession, Specialization, Trait, Skill, Weapon, Item
from tests.test_utils.gw2_mock import get_mock_gw2_response


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    # Mock execute to return a mock that can be chained with scalars()
    mock_result = AsyncMock()
    mock_scalars = AsyncMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    session.execute.return_value = mock_result
    session.get.return_value = None
    
    # Mock add and commit
    session.add = AsyncMock()
    session.commit = AsyncMock()
    return session


async def mock_get(url, **kwargs):
    """Mock GET request handler."""
    if 'professions' in url:
        return {'Guardian': {'name': 'Guardian', 'icon': 'test.png'}}
    elif 'specializations' in url:
        return [{'id': 1, 'name': 'Test Spec', 'profession': 'Guardian', 'major_traits': [1, 2, 3]}]
    elif 'traits' in url:
        return {'id': 1, 'name': 'Test Trait', 'description': 'Test Description'}
    elif 'skills' in url:
        return {'id': 1, 'name': 'Test Skill', 'description': 'Test Description'}
    elif 'items' in url:
        return {'id': 1, 'name': 'Test Item', 'type': 'Weapon', 'details': {'type': 'Axe'}}
    return {}

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_client = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = mock_get
        yield mock_client


class TestGW2SyncService:
    """Test the GW2 sync service."""

    @pytest.mark.asyncio
    async def test_sync_professions(self, mock_session, mock_http_client):
        """Test syncing professions from the GW2 API."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Mock the API responses
        mock_profession_ids = ["Guardian", "Warrior"]
        mock_profession_data = {
            "id": "Guardian",
            "name": "Guardian",
            "icon": "https://example.com/guardian.png",
            "description": "Test profession description",
            "weapons": {
                "Sword": {"specialization": 1, "flags": ["Mainhand"], "skills": [1, 2]}
            },
            "skills": [{"id": 1, "name": "Strike"}]
        }
        
        # Mock the _make_request method to return different responses based on the endpoint
        async def mock_make_request(endpoint, **kwargs):
            if endpoint == "professions":
                return mock_profession_ids
            elif endpoint.startswith("professions/"):
                return mock_profession_data
            return None
        
        with patch.object(service, '_make_request', side_effect=mock_make_request):
            # Test
            result = await service.sync_professions()
            
            # Assertions
            assert isinstance(result, list)  # Should return a list of professions
            assert len(result) > 0  # Should have processed at least one profession
            mock_session.add.assert_called()  # Should have added records to the session
            mock_session.commit.assert_awaited()  # Should have committed the transaction

    @pytest.mark.asyncio
    async def test_sync_specializations(self, mock_session, mock_http_client):
        """Test syncing specializations from the GW2 API."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Mock the API responses
        mock_specialization_ids = [6, 7, 8]
        mock_specialization_data = {
            "id": 6,
            "name": "Zeal",
            "profession": "Guardian",
            "elite": False,
            "minor_traits": [642, 653, 654],
            "major_traits": [655, 656, 657],
            "weapon_trait": 658,
            "icon": "https://example.com/zeal.png",
            "background": "Zeal specialization background"
        }
        
        # Mock the profession
        mock_profession = MagicMock()
        mock_profession.id = "Guardian"
        mock_profession.code = "Guardian"
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profession
        mock_session.execute.return_value = mock_result
        
        # Mock the _make_request method to return different responses based on the endpoint
        async def mock_make_request(endpoint, **kwargs):
            if endpoint == "specializations":
                return mock_specialization_ids
            elif endpoint.startswith("specializations/"):
                return mock_specialization_data
            return None
        
        with patch.object(service, '_make_request', side_effect=mock_make_request):
            # Test sync_specializations without arguments
            result = await service.sync_specializations()
            
            # Assertions
            assert isinstance(result, list)  # Should return a list of specializations
            assert len(result) > 0  # Should have processed at least one specialization
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_skills(self, mock_session, mock_http_client):
        """Test syncing skills from the GW2 API."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Mock the API responses
        mock_skill_ids = [9093, 9098, 9102]
        mock_skill_data = {
            "id": 9093,
            "name": "Strike",
            "description": "Strike your foe with a mighty blow.",
            "icon": "https://example.com/strike.png",
            "type": "Weapon",
            "weapon_type": "Sword",
            "slot": "Weapon_1",
            "facts": [
                {
                    "type": "Damage",
                    "hit_count": 1,
                    "dmg_multiplier": 0.7
                },
                {
                    "type": "Buff",
                    "status": "Might",
                    "duration": 5,
                    "description": "Increased damage",
                    "apply_count": 1
                }
            ]
        }
        
        # Mock the _make_request method to return different responses based on the endpoint
        async def mock_make_request(endpoint, **kwargs):
            if endpoint == "skills":
                return mock_skill_ids
            elif endpoint.startswith("skills/"):
                return mock_skill_data
            return None
        
        with patch.object(service, '_make_request', side_effect=mock_make_request):
            # Test sync_skills without arguments
            result = await service.sync_skills()
            
            # Assertions
            assert isinstance(result, list)  # Should return a list of skills
            assert len(result) > 0  # Should have processed at least one skill
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_traits(self, mock_session, mock_http_client):
        """Test syncing traits from the GW2 API."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Mock the API responses
        mock_trait_ids = [642, 653, 654, 655, 656, 657]
        mock_trait_data = {
            "id": 642,
            "name": "Zealous Blade",
            "description": "Gain life force when you hit an enemy with a melee weapon.",
            "icon": "https://example.com/zealous_blade.png",
            "slot": "Minor",
            "specialization": 6,
            "tier": 1,
            "facts": [
                {
                    "type": "AttributeAdjust",
                    "value": 100,
                    "target": "Healing"
                }
            ],
            "traited_facts": []
        }
        
        # Mock the specialization
        mock_spec = MagicMock()
        mock_spec.id = 6
        
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_spec
        mock_session.execute.return_value = mock_result
        
        # Mock the _make_request method to return different responses based on the endpoint
        async def mock_make_request(endpoint, **kwargs):
            if endpoint == "traits":
                return mock_trait_ids
            elif endpoint.startswith("traits/"):
                return mock_trait_data
            return None
        
        with patch.object(service, '_make_request', side_effect=mock_make_request):
            # Test sync_traits without arguments
            result = await service.sync_traits()
            
            # Assertions
            assert isinstance(result, list)  # Should return a list of traits
            assert len(result) > 0  # Should have processed at least one trait
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_items(self, mock_session, mock_http_client):
        """Test syncing items from the GW2 API."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Mock the API responses
        mock_item_ids = [1, 2, 3]
        mock_item_data = {
            "id": 1,
            "name": "Zojja's Greatsword",
            "type": "Weapon",
            "description": "A powerful ascended greatsword",
            "icon": "https://example.com/greatsword.png",
            "level": 80,
            "rarity": "Ascended",
            "vendor_value": 1000,
            "details": {
                "type": "Greatsword",
                "damage_type": "Physical",
                "min_power": 1,
                "max_power": 1000,
                "defense": 0,
                "infusion_slots": [],
                "infix_upgrade": {
                    "id": 1,
                    "attributes": [
                        {"attribute": "Power", "modifier": 179},
                        {"attribute": "Precision", "modifier": 179}
                    ]
                },
                "suffix_item_id": 1,
                "secondary_suffix_item_id": ""
            }
        }
        
        # Mock the _make_request method to return different responses based on the endpoint
        async def mock_make_request(endpoint, **kwargs):
            if endpoint == "items":
                return mock_item_ids
            elif endpoint.startswith("items/"):
                return mock_item_data
            return None
        
        with patch.object(service, '_make_request', side_effect=mock_make_request):
            # Test sync_items without arguments
            result = await service.sync_items()
            
            # Assertions
            assert isinstance(result, list)  # Should return a list of items
            assert len(result) > 0  # Should have processed at least one item
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_weapons(self, mock_session, mock_http_client):
        """Test syncing weapons from the GW2 API."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Mock the API responses
        mock_weapon_ids = [1, 2, 3]
        mock_weapon_data = {
            "id": 1,
            "name": "Greatsword",
            "type": "Weapon",
            "description": "A powerful greatsword",
            "icon": "https://example.com/greatsword.png",
            "details": {
                "type": "Greatsword",
                "damage_type": "Physical",
                "min_power": 900,
                "max_power": 1100,
                "flags": ["TwoHand"],
                "skills": [
                    {"id": 1, "name": "Strike"},
                    {"id": 2, "name": "Slash"}
                ]
            }
        }
        
        # Mock the skills
        mock_skill = MagicMock()
        mock_skill.id = 1
        mock_skill.name = "Strike"
        
        # Mock the database query results
        mock_weapon_result = MagicMock()
        mock_weapon_result.scalars.return_value.all.return_value = [mock_skill]
        
        mock_skills_result = MagicMock()
        mock_skills_result.scalars.return_value.all.return_value = [mock_skill]
        
        mock_session.execute.side_effect = [mock_weapon_result, mock_skills_result]
        
        # Mock the _make_request method to return different responses based on the endpoint
        async def mock_make_request(endpoint, **kwargs):
            if endpoint == "weapons":
                return mock_weapon_ids
            elif endpoint.startswith("weapons/"):
                return mock_weapon_data
            return None
        
        with patch.object(service, '_make_request', side_effect=mock_make_request):
            # Test sync_weapons without arguments
            result = await service.sync_weapons()
            
            # Assertions
            assert isinstance(result, list)  # Should return a list of weapons
            assert len(result) > 0  # Should have processed at least one weapon
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_full_sync(self, mock_session, mock_http_client):
        """Test a full synchronization of all GW2 data."""
        # Setup
        service = GW2SyncService(mock_session)
        
        # Create mock professions for the test
        mock_profession = Profession(id="Guardian", name="Guardian")
        
        # Mock all the sync methods with the correct return values
        with patch.object(service, 'sync_professions', return_value=[mock_profession]) as mock_sync_professions, \
             patch.object(service, 'sync_specializations', return_value=[]) as mock_sync_specs, \
             patch.object(service, 'sync_skills', return_value=[]) as mock_sync_skills, \
             patch.object(service, 'sync_traits', return_value=[]) as mock_sync_traits, \
             patch.object(service, 'sync_items', return_value=[]) as mock_sync_items, \
             patch.object(service, 'sync_weapons', return_value=[]) as mock_sync_weapons:
            
            # Test sync_all
            await service.sync_all()
            
            # Assert all sync methods were called
            mock_sync_professions.assert_awaited_once()
            mock_sync_specs.assert_awaited_once()
            mock_sync_skills.assert_awaited_once()
            mock_sync_traits.assert_awaited_once()
            mock_sync_items.assert_awaited_once()
            mock_sync_weapons.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_gw2_data(mock_session, mock_http_client):
    """Test the convenience function for syncing GW2 data."""
    # Create a mock profession for the test
    mock_profession = Profession(id="Guardian", name="Guardian")
    
    # Mock the GW2SyncService context manager
    mock_service = AsyncMock()
    mock_service.sync_all = AsyncMock(return_value=[mock_profession])
    
    # Mock the async context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_service
    
    with patch('app.services.gw2_sync_service.GW2SyncService', return_value=mock_context) as mock_gw2_sync_service:
        # Test
        from app.services.gw2_sync_service import sync_gw2_data
        result = await sync_gw2_data(mock_session)
        
        # Assertions
        mock_gw2_sync_service.assert_called_once_with(mock_session)
        mock_context.__aenter__.assert_awaited_once()
        mock_service.sync_all.assert_awaited_once()
        mock_context.__aexit__.assert_awaited_once_with(None, None, None)
        
        # Verify the result is the return value of sync_all
        assert result == [mock_profession]
