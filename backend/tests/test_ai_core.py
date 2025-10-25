"""
Tests unitaires pour AI Core v4.1.0

Coverage ciblé: >= 80%

Teste:
    - Génération compositions (Mistral + fallback)
    - Feature flags
    - Timeout handling
    - Error handling
    - Team size auto-adaptation
    - Logs structurés
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from app.ai.core import GW2AICore, GameMode, TeamComposition, get_ai_core
from app.core.config import settings


class TestGameMode:
    """Tests pour GameMode enum"""
    
    def test_game_mode_values(self):
        """Vérifie que tous les modes de jeu sont définis"""
        assert GameMode.ZERG.value == "zerg"
        assert GameMode.RAID.value == "raid"
        assert GameMode.FRACTALS.value == "fractals"
        assert GameMode.ROAMING.value == "roaming"
        assert GameMode.STRIKES.value == "strikes"


class TestTeamComposition:
    """Tests pour TeamComposition"""
    
    def test_composition_creation(self):
        """Teste la création d'une composition"""
        comp = TeamComposition(
            name="Test Comp",
            size=10,
            game_mode=GameMode.RAID,
            builds=[{"profession": "Guardian", "count": 2}],
            strategy="Test strategy",
            strengths=["str1", "str2"],
            weaknesses=["weak1"],
            synergy_score=8.5
        )
        
        assert comp.name == "Test Comp"
        assert comp.size == 10
        assert comp.game_mode == GameMode.RAID
        assert len(comp.builds) == 1
        assert comp.synergy_score == 8.5
        assert comp.id is not None
        assert comp.timestamp is not None
    
    def test_composition_to_dict(self):
        """Teste la conversion en dictionnaire"""
        comp = TeamComposition(
            name="Test Comp",
            size=10,
            game_mode=GameMode.RAID,
            builds=[],
            strategy="Test",
            strengths=[],
            weaknesses=[]
        )
        
        comp_dict = comp.to_dict()
        
        assert comp_dict["name"] == "Test Comp"
        assert comp_dict["size"] == 10
        assert comp_dict["game_mode"] == "raid"
        assert "id" in comp_dict
        assert "timestamp" in comp_dict


class TestGW2AICore:
    """Tests pour GW2AICore"""
    
    @pytest.fixture
    def ai_core(self):
        """Fixture pour créer une instance AI Core"""
        return GW2AICore()
    
    @pytest.mark.asyncio
    async def test_initialize(self, ai_core):
        """Teste l'initialisation"""
        await ai_core.initialize()
        
        assert ai_core._is_initialized is True
        assert ai_core._client is not None
        
        await ai_core.close()
    
    @pytest.mark.asyncio
    async def test_close(self, ai_core):
        """Teste la fermeture"""
        await ai_core.initialize()
        await ai_core.close()
        
        assert ai_core._is_initialized is False
        assert ai_core._client is None
    
    @pytest.mark.asyncio
    async def test_team_size_auto_adaptation(self, ai_core):
        """Teste l'auto-adaptation de la taille d'équipe"""
        # Mock fallback to avoid external calls
        ai_core.mistral_api_key = None
        
        # Test each game mode
        comp_zerg = await ai_core.compose_team(GameMode.ZERG)
        assert comp_zerg.size == 50
        
        comp_raid = await ai_core.compose_team(GameMode.RAID)
        assert comp_raid.size == 10
        
        comp_fractals = await ai_core.compose_team(GameMode.FRACTALS)
        assert comp_fractals.size == 5
        
        comp_roaming = await ai_core.compose_team(GameMode.ROAMING)
        assert comp_roaming.size == 5
        
        comp_strikes = await ai_core.compose_team(GameMode.STRIKES)
        assert comp_strikes.size == 10
    
    @pytest.mark.asyncio
    async def test_compose_team_with_custom_size(self, ai_core):
        """Teste la composition avec taille personnalisée"""
        ai_core.mistral_api_key = None  # Force fallback
        
        comp = await ai_core.compose_team(
            game_mode=GameMode.RAID,
            team_size=15
        )
        
        assert comp.size == 15
        assert comp.game_mode == GameMode.RAID
    
    @pytest.mark.asyncio
    async def test_compose_team_invalid_mode(self, ai_core):
        """Teste le rejet d'un mode de jeu invalide"""
        with pytest.raises(ValueError, match="Invalid game mode"):
            await ai_core.compose_team(game_mode="invalid_mode")
    
    @pytest.mark.asyncio
    async def test_compose_team_string_mode(self, ai_core):
        """Teste la conversion string → enum"""
        ai_core.mistral_api_key = None
        
        comp = await ai_core.compose_team(game_mode="zerg")
        assert comp.game_mode == GameMode.ZERG
    
    @pytest.mark.asyncio
    async def test_fallback_composition(self, ai_core):
        """Teste la génération fallback"""
        comp = await ai_core._generate_fallback_composition(
            game_mode=GameMode.ZERG,
            team_size=50,
            preferences=None,
            request_id="test-123"
        )
        
        assert comp.name == "Standard Zerg Composition"
        assert comp.size == 50
        assert comp.game_mode == GameMode.ZERG
        assert len(comp.builds) > 0
        assert comp.metadata["source"] == "rule_based_fallback"
        assert comp.metadata["request_id"] == "test-123"
        assert comp.synergy_score == 7.5
    
    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self, ai_core):
        """Teste le comportement quand AI Core est désactivé"""
        with patch.object(settings, 'AI_CORE_ENABLED', False):
            comp = await ai_core.compose_team(GameMode.RAID)
            
            assert comp.metadata["source"] == "rule_based_fallback"
    
    @pytest.mark.asyncio
    async def test_mistral_generation_success(self, ai_core):
        """Teste la génération avec Mistral AI (succès)"""
        # Setup
        ai_core.mistral_api_key = "test_key"
        await ai_core.initialize()
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '''
                    {
                        "name": "Mistral Test Comp",
                        "builds": [
                            {
                                "profession": "Guardian",
                                "role": "Support",
                                "count": 2
                            }
                        ],
                        "strategy": "Test strategy",
                        "strengths": ["str1"],
                        "weaknesses": ["weak1"],
                        "synergy_score": 9.0
                    }
                    '''
                }
            }]
        }
        
        # Patch HTTP client
        with patch.object(ai_core._client, 'post', return_value=mock_response):
            comp = await ai_core.compose_team(
                game_mode=GameMode.RAID,
                team_size=10
            )
            
            assert comp.name == "Mistral Test Comp"
            assert comp.metadata["source"] == "mistral_ai"
            assert comp.metadata["model"] == ai_core.MISTRAL_MODEL
            assert comp.synergy_score == 9.0
        
        await ai_core.close()
    
    @pytest.mark.asyncio
    async def test_mistral_generation_failure_with_fallback(self, ai_core):
        """Teste le fallback quand Mistral échoue"""
        ai_core.mistral_api_key = "test_key"
        ai_core.fallback_enabled = True
        await ai_core.initialize()
        
        # Mock HTTP error
        with patch.object(
            ai_core._client,
            'post',
            side_effect=httpx.HTTPError("Connection failed")
        ):
            comp = await ai_core.compose_team(
                game_mode=GameMode.RAID,
                team_size=10
            )
            
            # Should fallback to rule-based
            assert comp.metadata["source"] == "rule_based_fallback"
        
        await ai_core.close()
    
    @pytest.mark.asyncio
    async def test_mistral_generation_failure_without_fallback(self, ai_core):
        """Teste le rejet quand Mistral échoue et fallback désactivé"""
        ai_core.mistral_api_key = "test_key"
        ai_core.fallback_enabled = False
        await ai_core.initialize()
        
        # Mock HTTP error
        with patch.object(
            ai_core._client,
            'post',
            side_effect=httpx.HTTPError("Connection failed")
        ):
            with pytest.raises(httpx.HTTPError):
                await ai_core.compose_team(
                    game_mode=GameMode.RAID,
                    team_size=10
                )
        
        await ai_core.close()
    
    @pytest.mark.asyncio
    async def test_parse_mistral_response(self, ai_core):
        """Teste le parsing de la réponse Mistral"""
        content = '''
        Here is the composition:
        {
            "name": "Test",
            "builds": [],
            "strategy": "Test",
            "strengths": [],
            "weaknesses": [],
            "synergy_score": 8.0
        }
        Some text after
        '''
        
        result = ai_core._parse_mistral_response(content)
        
        assert result["name"] == "Test"
        assert result["synergy_score"] == 8.0
    
    @pytest.mark.asyncio
    async def test_parse_mistral_response_no_json(self, ai_core):
        """Teste le parsing quand pas de JSON"""
        content = "No JSON here"
        
        with pytest.raises(ValueError, match="No JSON found"):
            ai_core._parse_mistral_response(content)
    
    def test_get_mode_ratios(self, ai_core):
        """Teste les ratios par mode de jeu"""
        # Test all modes have ratios
        for mode in GameMode:
            ratios = ai_core._get_mode_ratios(mode)
            assert len(ratios) > 0
            assert all("profession" in r for r in ratios)
            assert all("ratio" in r for r in ratios)
    
    def test_create_mistral_prompt(self, ai_core):
        """Teste la création du prompt Mistral"""
        prompt = ai_core._create_mistral_prompt(
            game_mode=GameMode.RAID,
            team_size=10,
            preferences={"focus": "boons"}
        )
        
        assert "raid" in prompt.lower()
        assert "10 players" in prompt
        assert "focus" in prompt
        assert "JSON format" in prompt
    
    @pytest.mark.asyncio
    async def test_preferences_passed_to_composition(self, ai_core):
        """Teste que les préférences sont incluses dans la composition"""
        ai_core.mistral_api_key = None
        
        preferences = {"focus": "damage", "avoid": ["Necromancer"]}
        comp = await ai_core.compose_team(
            game_mode=GameMode.RAID,
            preferences=preferences
        )
        
        assert comp.metadata["preferences"] == preferences
    
    @pytest.mark.asyncio
    async def test_request_id_in_logs(self, ai_core):
        """Teste que request_id est présent dans les métadonnées"""
        ai_core.mistral_api_key = None
        
        comp = await ai_core.compose_team(
            game_mode=GameMode.RAID,
            request_id="custom-request-123"
        )
        
        assert comp.metadata["request_id"] == "custom-request-123"


class TestSingleton:
    """Tests pour le singleton get_ai_core()"""
    
    @pytest.mark.asyncio
    async def test_get_ai_core_singleton(self):
        """Teste que get_ai_core() retourne la même instance"""
        core1 = await get_ai_core()
        core2 = await get_ai_core()
        
        assert core1 is core2
    
    @pytest.mark.asyncio
    async def test_get_ai_core_initialized(self):
        """Teste que l'instance retournée est initialisée"""
        core = await get_ai_core()
        
        assert core._is_initialized is True
        assert core._client is not None


# Coverage report helper
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.ai.core", "--cov-report=term-missing"])
