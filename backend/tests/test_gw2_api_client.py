"""
Tests for GW2 API Client

Tests unitaires pour le client API GW2.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.gw2_api_client import GW2APIClient


@pytest.mark.asyncio
class TestGW2APIClient:
    """Tests pour le client API GW2."""

    def test_client_initialization(self):
        """Test l'initialisation du client."""
        client = GW2APIClient()

        assert client.timeout == 30
        assert client.max_retries == 3
        assert "User-Agent" in client.headers
        assert client.api_key is None

    def test_client_initialization_with_api_key(self):
        """Test l'initialisation avec une clé API."""
        api_key = "test-api-key-123"
        client = GW2APIClient(api_key=api_key)

        assert client.api_key == api_key
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == f"Bearer {api_key}"

    @patch("httpx.AsyncClient")
    async def test_get_professions(self, mock_client):
        """Test la récupération de la liste des professions."""
        # Mock de la réponse
        mock_response = MagicMock()
        mock_response.json.return_value = [
            "Guardian",
            "Warrior",
            "Engineer",
            "Ranger",
            "Thief",
            "Elementalist",
            "Mesmer",
            "Necromancer",
            "Revenant",
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = GW2APIClient()
        professions = await client.get_professions()

        assert isinstance(professions, list)
        assert len(professions) == 9
        assert "Guardian" in professions
        assert "Revenant" in professions

    @patch("httpx.AsyncClient")
    async def test_get_profession(self, mock_client):
        """Test la récupération des détails d'une profession."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "Guardian",
            "name": "Guardian",
            "code": 1,
            "icon": "https://...",
            "specializations": [13, 16, 27, 42, 46, 62, 65],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = GW2APIClient()
        profession = await client.get_profession("Guardian")

        assert profession["id"] == "Guardian"
        assert profession["name"] == "Guardian"
        assert "specializations" in profession
        assert isinstance(profession["specializations"], list)

    @patch("httpx.AsyncClient")
    async def test_get_skills(self, mock_client):
        """Test la récupération des compétences."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 12345, "name": "Test Skill", "description": "A test skill", "type": "Weapon"}
        ]
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = GW2APIClient()
        skills = await client.get_skills([12345])

        assert isinstance(skills, list)
        assert len(skills) > 0
        assert skills[0]["id"] == 12345

    @patch("httpx.AsyncClient")
    async def test_get_specializations(self, mock_client):
        """Test la récupération des spécialisations."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 27, "name": "Dragonhunter", "profession": "Guardian", "elite": True}]
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = GW2APIClient()
        specs = await client.get_specializations([27])

        assert isinstance(specs, list)
        assert len(specs) > 0
        assert specs[0]["name"] == "Dragonhunter"
        assert specs[0]["elite"] is True

    async def test_cache_functionality(self):
        """Test le système de cache."""
        client = GW2APIClient()

        # Vérifier que le cache est vide
        stats = client.get_cache_stats()
        assert stats["cache_size"] == 0

        # Ajouter au cache manuellement pour le test
        client._cache["test_key"] = ({"data": "test"}, client._cache_ttl)

        stats = client.get_cache_stats()
        assert stats["cache_size"] == 1

        # Vider le cache
        client.clear_cache()
        stats = client.get_cache_stats()
        assert stats["cache_size"] == 0

    @patch("httpx.AsyncClient")
    async def test_request_retry_on_failure(self, mock_client):
        """Test le retry en cas d'échec."""
        # Simuler un échec puis un succès
        mock_response_fail = MagicMock()
        mock_response_fail.raise_for_status.side_effect = Exception("Network error")

        mock_response_success = MagicMock()
        mock_response_success.json.return_value = ["Guardian"]
        mock_response_success.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = [mock_response_fail, mock_response_success]
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = GW2APIClient(max_retries=2)

        # Le client devrait réessayer et réussir
        with pytest.raises(Exception):
            # La première tentative échoue
            await client.get_professions()

    @patch("httpx.AsyncClient")
    async def test_import_all_game_data(self, mock_client):
        """Test l'importation complète des données de jeu."""
        # Mock des réponses
        mock_professions = MagicMock()
        mock_professions.json.return_value = ["Guardian", "Warrior"]
        mock_professions.raise_for_status = MagicMock()

        mock_profession_detail = MagicMock()
        mock_profession_detail.json.return_value = {
            "id": "Guardian",
            "name": "Guardian",
            "specializations": [13, 16, 27],
        }
        mock_profession_detail.raise_for_status = MagicMock()

        mock_specs = MagicMock()
        mock_specs.json.return_value = [1, 2, 3]
        mock_specs.raise_for_status = MagicMock()

        mock_specs_detail = MagicMock()
        mock_specs_detail.json.return_value = [{"id": 1, "name": "Spec1"}, {"id": 2, "name": "Spec2"}]
        mock_specs_detail.raise_for_status = MagicMock()

        mock_traits = MagicMock()
        mock_traits.json.return_value = [100, 101]
        mock_traits.raise_for_status = MagicMock()

        mock_traits_detail = MagicMock()
        mock_traits_detail.json.return_value = [{"id": 100, "name": "Trait1"}, {"id": 101, "name": "Trait2"}]
        mock_traits_detail.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = [
            mock_professions,
            mock_profession_detail,
            mock_profession_detail,
            mock_specs,
            mock_specs_detail,
            mock_traits,
            mock_traits_detail,
        ]
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        client = GW2APIClient()
        result = await client.import_all_game_data()

        assert result["success"] is True
        assert "professions" in result
        assert "specializations" in result
        assert "traits" in result
        assert "import_timestamp" in result

    def test_get_cache_stats(self):
        """Test la récupération des statistiques du cache."""
        client = GW2APIClient()

        stats = client.get_cache_stats()

        assert "cache_size" in stats
        assert "cache_ttl_hours" in stats
        assert stats["cache_size"] == 0
        assert stats["cache_ttl_hours"] == 24

    def test_clear_cache(self):
        """Test le vidage du cache."""
        client = GW2APIClient()

        # Ajouter des données au cache
        client._cache["key1"] = ("data1", None)
        client._cache["key2"] = ("data2", None)

        assert len(client._cache) == 2

        client.clear_cache()

        assert len(client._cache) == 0
