"""
GW2 AI Core - Moteur IA Central v4.1.0

Ce module agit comme cerveau unique du système IA.
Il centralise toute la logique de génération de compositions,
analyse de synergies, et apprentissage ML.

Architecture:
    - Mistral AI: Génération compositions intelligentes
    - ML Local: Prédiction synergies (à implémenter Phase 2)
    - Context Service: Veille web méta GW2 (à implémenter Phase 4)
    - Rule-based Fallback: Compositions par défaut

Feature Flags:
    - AI_CORE_ENABLED: Active/désactive ce module
    - ML_TRAINING_ENABLED: Active apprentissage ML
    - AI_FALLBACK_ENABLED: Active fallback rule-based
"""

import uuid
import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from app.core.logging import logger
from app.core.config import settings


class GameMode(str, Enum):
    """Modes de jeu GW2"""
    ZERG = "zerg"
    RAID = "raid"
    FRACTALS = "fractals"
    ROAMING = "roaming"
    STRIKES = "strikes"


class TeamComposition:
    """Représentation d'une composition d'équipe"""
    
    def __init__(
        self,
        name: str,
        size: int,
        game_mode: GameMode,
        builds: List[Dict[str, Any]],
        strategy: str,
        strengths: List[str],
        weaknesses: List[str],
        synergy_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.size = size
        self.game_mode = game_mode
        self.builds = builds
        self.strategy = strategy
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.synergy_score = synergy_score
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "game_mode": self.game_mode.value,
            "builds": self.builds,
            "strategy": self.strategy,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "synergy_score": self.synergy_score,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class GW2AICore:
    """
    Moteur IA Central pour GW2Optimizer
    
    Responsabilités:
        - Génération compositions équipes
        - Analyse synergies
        - Apprentissage ML (Phase 2)
        - Context awareness (Phase 4)
    
    Example:
        ```python
        ai_core = GW2AICore()
        await ai_core.initialize()
        
        composition = await ai_core.compose_team(
            game_mode=GameMode.ZERG,
            team_size=None,  # Auto-adapté
            preferences={"focus": "boons"}
        )
        
        print(f"Composition: {composition.name}")
        print(f"Synergy Score: {composition.synergy_score}/10")
        ```
    """
    
    # URL Mistral AI API
    MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
    MISTRAL_MODEL = "mistral-large-latest"
    
    # Team sizes par mode de jeu
    DEFAULT_TEAM_SIZES = {
        GameMode.ZERG: 50,
        GameMode.RAID: 10,
        GameMode.FRACTALS: 5,
        GameMode.ROAMING: 5,
        GameMode.STRIKES: 10
    }
    
    def __init__(self):
        """Initialise le moteur IA"""
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.timeout = settings.AI_TIMEOUT
        self.fallback_enabled = settings.AI_FALLBACK_ENABLED
        self._client: Optional[httpx.AsyncClient] = None
        self._is_initialized = False
        
        logger.info(
            "🤖 AI Core initialized",
            extra={
                "ai_core_enabled": settings.AI_CORE_ENABLED,
                "mistral_configured": bool(self.mistral_api_key),
                "timeout": self.timeout,
                "fallback_enabled": self.fallback_enabled
            }
        )
    
    async def initialize(self) -> None:
        """Initialise le client HTTP"""
        if self._is_initialized:
            logger.warning("⚠️  AI Core already initialized")
            return
        
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self._is_initialized = True
        logger.info("✅ AI Core client initialized")
    
    async def close(self) -> None:
        """Ferme le client HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._is_initialized = False
            logger.info("🔒 AI Core client closed")
    
    async def compose_team(
        self,
        game_mode: GameMode | str,
        team_size: Optional[int] = None,
        preferences: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> TeamComposition:
        """
        Génère une composition d'équipe optimale
        
        Args:
            game_mode: Mode de jeu (zerg, raid, fractals, roaming, strikes)
            team_size: Taille équipe (None = auto-adapté selon mode)
            preferences: Préférences utilisateur (focus, classes préférées, etc.)
            request_id: ID de requête pour logs structurés
        
        Returns:
            TeamComposition: Composition générée avec métadonnées
        
        Raises:
            ValueError: Si mode de jeu invalide
        """
        # Generate request ID for observability
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Convert string to enum if needed
        if isinstance(game_mode, str):
            try:
                game_mode = GameMode(game_mode.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid game mode: {game_mode}. "
                    f"Valid modes: {[m.value for m in GameMode]}"
                )
        
        # Auto-adapt team size if not provided
        if team_size is None:
            team_size = self.DEFAULT_TEAM_SIZES.get(game_mode, 10)
        
        logger.info(
            "🎯 Composing team",
            extra={
                "request_id": request_id,
                "game_mode": game_mode.value,
                "team_size": team_size,
                "preferences": preferences,
                "ai_core_enabled": settings.AI_CORE_ENABLED
            }
        )
        
        # Feature flag check
        if not settings.AI_CORE_ENABLED:
            logger.warning(
                "⚠️  AI Core disabled, using fallback",
                extra={"request_id": request_id}
            )
            return await self._generate_fallback_composition(
                game_mode, team_size, preferences, request_id
            )
        
        # Try Mistral AI generation
        if self.mistral_api_key:
            try:
                composition = await self._generate_with_mistral(
                    game_mode, team_size, preferences, request_id
                )
                
                # Phase 2: Enhance score with ML model
                composition = await self._enhance_with_ml(composition, request_id)
                
                # Save composition for future training
                await self._save_composition(composition)
                
                logger.info(
                    "✅ Team composition generated with Mistral + ML",
                    extra={
                        "request_id": request_id,
                        "composition_id": composition.id,
                        "synergy_score": composition.synergy_score,
                        "source": "mistral_ai_ml"
                    }
                )
                
                return composition
                
            except Exception as e:
                logger.error(
                    f"❌ Mistral generation failed: {str(e)}",
                    extra={
                        "request_id": request_id,
                        "error": str(e),
                        "fallback": self.fallback_enabled
                    }
                )
                
                if not self.fallback_enabled:
                    raise
        
        # Fallback to rule-based generation
        logger.info(
            "📋 Using rule-based fallback",
            extra={"request_id": request_id}
        )
        
        return await self._generate_fallback_composition(
            game_mode, team_size, preferences, request_id
        )
    
    async def _generate_with_mistral(
        self,
        game_mode: GameMode,
        team_size: int,
        preferences: Optional[Dict[str, Any]],
        request_id: str
    ) -> TeamComposition:
        """Génère composition avec Mistral AI"""
        
        if not self._is_initialized:
            await self.initialize()
        
        # Create prompt
        prompt = self._create_mistral_prompt(game_mode, team_size, preferences)
        
        # Call Mistral API
        response = await self._client.post(
            self.MISTRAL_API_URL,
            headers={
                "Authorization": f"Bearer {self.mistral_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.MISTRAL_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Guild Wars 2 strategist specializing in "
                            "WvW, raids, fractals, and strikes. Generate optimal team "
                            "compositions with detailed reasoning."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Extract JSON
        composition_data = self._parse_mistral_response(content)
        
        # Create TeamComposition object
        composition = TeamComposition(
            name=composition_data.get("name", f"{game_mode.value.capitalize()} Composition"),
            size=team_size,
            game_mode=game_mode,
            builds=composition_data.get("builds", []),
            strategy=composition_data.get("strategy", ""),
            strengths=composition_data.get("strengths", []),
            weaknesses=composition_data.get("weaknesses", []),
            synergy_score=composition_data.get("synergy_score", 0.0),
            metadata={
                "source": "mistral_ai",
                "model": self.MISTRAL_MODEL,
                "request_id": request_id,
                "preferences": preferences
            }
        )
        
        return composition
    
    def _create_mistral_prompt(
        self,
        game_mode: GameMode,
        team_size: int,
        preferences: Optional[Dict[str, Any]]
    ) -> str:
        """Crée le prompt pour Mistral AI"""
        
        prefs_str = ""
        if preferences:
            prefs_str = f"\nUser Preferences: {json.dumps(preferences, indent=2)}"
        
        return f"""
Generate an optimal Guild Wars 2 team composition for {game_mode.value} mode.

Team Size: {team_size} players{prefs_str}

Requirements:
1. Balanced composition with tanks, supports, and DPS
2. Strong boon coverage (might, fury, quickness, alacrity, stability)
3. Good crowd control capabilities
4. Mobility for rotations
5. Synergy between professions

Provide the composition in JSON format:
{{
    "name": "Composition name",
    "builds": [
        {{
            "profession": "Guardian",
            "specialization": "Firebrand",
            "role": "Support",
            "count": X,
            "priority": "High|Medium|Low",
            "description": "Brief role description",
            "key_boons": ["Stability", "Aegis", "Quickness"]
        }}
    ],
    "strategy": "Overall strategy description",
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "synergy_score": 8.5
}}
"""
    
    def _parse_mistral_response(self, content: str) -> Dict[str, Any]:
        """Parse la réponse de Mistral AI"""
        
        try:
            # Extract JSON from response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in Mistral response")
        
        except Exception as e:
            logger.error(f"Failed to parse Mistral response: {str(e)}")
            raise
    
    async def _generate_fallback_composition(
        self,
        game_mode: GameMode,
        team_size: int,
        preferences: Optional[Dict[str, Any]],
        request_id: str
    ) -> TeamComposition:
        """
        Génère composition rule-based (fallback)
        
        Cette méthode utilise des ratios prédéfinis optimaux
        pour chaque mode de jeu.
        """
        
        # Ratios optimaux par mode
        ratios = self._get_mode_ratios(game_mode)
        
        # Generate builds
        builds = []
        for build_template in ratios:
            count = int(team_size * build_template["ratio"])
            if count > 0:
                builds.append({
                    "profession": build_template["profession"],
                    "specialization": build_template.get("specialization", ""),
                    "role": build_template["role"],
                    "count": count,
                    "priority": build_template.get("priority", "Medium"),
                    "description": build_template["description"],
                    "key_boons": build_template.get("key_boons", [])
                })
        
        # Create composition
        composition = TeamComposition(
            name=f"Standard {game_mode.value.capitalize()} Composition",
            size=team_size,
            game_mode=game_mode,
            builds=builds,
            strategy=f"Balanced {game_mode.value} composition with strong boon coverage and synergies",
            strengths=[
                "Excellent boon coverage",
                "Balanced damage and survivability",
                "Good crowd control",
                "Proven effectiveness"
            ],
            weaknesses=[
                "May lack flexibility for specific encounters",
                "Requires coordination",
                "Generic approach"
            ],
            synergy_score=7.5,
            metadata={
                "source": "rule_based_fallback",
                "request_id": request_id,
                "preferences": preferences
            }
        )
        
        return composition
    
    def _get_mode_ratios(self, game_mode: GameMode) -> List[Dict[str, Any]]:
        """Retourne les ratios optimaux pour un mode de jeu"""
        
        ratios = {
            GameMode.ZERG: [
                {
                    "profession": "Guardian",
                    "specialization": "Firebrand",
                    "role": "Support",
                    "ratio": 0.20,
                    "priority": "High",
                    "description": "Stability, healing, and boons",
                    "key_boons": ["Stability", "Aegis", "Quickness"]
                },
                {
                    "profession": "Warrior",
                    "specialization": "Spellbreaker",
                    "role": "Tank",
                    "ratio": 0.10,
                    "priority": "High",
                    "description": "Frontline tank with boon corrupt",
                    "key_boons": ["Might"]
                },
                {
                    "profession": "Necromancer",
                    "specialization": "Scourge",
                    "role": "DPS",
                    "ratio": 0.30,
                    "priority": "High",
                    "description": "AoE damage and boon corrupt",
                    "key_boons": ["Barrier"]
                },
                {
                    "profession": "Mesmer",
                    "specialization": "Chronomancer",
                    "role": "Support",
                    "ratio": 0.15,
                    "priority": "Medium",
                    "description": "Boons and portals",
                    "key_boons": ["Quickness", "Alacrity"]
                },
                {
                    "profession": "Revenant",
                    "specialization": "Herald",
                    "role": "DPS",
                    "ratio": 0.15,
                    "priority": "Medium",
                    "description": "Damage and boons",
                    "key_boons": ["Might", "Fury"]
                },
                {
                    "profession": "Engineer",
                    "specialization": "Scrapper",
                    "role": "Support",
                    "ratio": 0.10,
                    "priority": "Low",
                    "description": "Utility and cleanse",
                    "key_boons": ["Superspeed"]
                }
            ],
            GameMode.RAID: [
                {
                    "profession": "Guardian",
                    "specialization": "Firebrand",
                    "role": "Support",
                    "ratio": 0.20,
                    "priority": "High",
                    "description": "Quickness and aegis",
                    "key_boons": ["Quickness", "Aegis"]
                },
                {
                    "profession": "Mesmer",
                    "specialization": "Chronomancer",
                    "role": "Support",
                    "ratio": 0.20,
                    "priority": "High",
                    "description": "Alacrity and utility",
                    "key_boons": ["Alacrity", "Quickness"]
                },
                {
                    "profession": "Warrior",
                    "specialization": "Berserker",
                    "role": "DPS",
                    "ratio": 0.30,
                    "priority": "High",
                    "description": "High single-target DPS",
                    "key_boons": ["Might"]
                },
                {
                    "profession": "Revenant",
                    "specialization": "Renegade",
                    "role": "DPS",
                    "ratio": 0.20,
                    "priority": "Medium",
                    "description": "Alacrity and DPS",
                    "key_boons": ["Alacrity", "Might"]
                },
                {
                    "profession": "Necromancer",
                    "specialization": "Reaper",
                    "role": "DPS",
                    "ratio": 0.10,
                    "priority": "Low",
                    "description": "Cleave damage",
                    "key_boons": []
                }
            ],
            GameMode.FRACTALS: [
                {
                    "profession": "Guardian",
                    "specialization": "Firebrand",
                    "role": "Support",
                    "ratio": 0.40,
                    "priority": "High",
                    "description": "Quickness and aegis",
                    "key_boons": ["Quickness", "Aegis", "Stability"]
                },
                {
                    "profession": "Mesmer",
                    "specialization": "Chronomancer",
                    "role": "Support",
                    "ratio": 0.20,
                    "priority": "High",
                    "description": "Alacrity and utility",
                    "key_boons": ["Alacrity"]
                },
                {
                    "profession": "Warrior",
                    "specialization": "Berserker",
                    "role": "DPS",
                    "ratio": 0.20,
                    "priority": "Medium",
                    "description": "High burst DPS",
                    "key_boons": ["Might"]
                },
                {
                    "profession": "Revenant",
                    "specialization": "Renegade",
                    "role": "DPS",
                    "ratio": 0.20,
                    "priority": "Medium",
                    "description": "Alacrity and DPS",
                    "key_boons": ["Alacrity", "Might"]
                }
            ],
            GameMode.ROAMING: [
                {
                    "profession": "Mesmer",
                    "specialization": "Mirage",
                    "role": "DPS",
                    "ratio": 0.40,
                    "priority": "High",
                    "description": "High mobility and burst",
                    "key_boons": ["Might", "Fury"]
                },
                {
                    "profession": "Thief",
                    "specialization": "Deadeye",
                    "role": "DPS",
                    "ratio": 0.30,
                    "priority": "High",
                    "description": "Burst damage and stealth",
                    "key_boons": []
                },
                {
                    "profession": "Warrior",
                    "specialization": "Spellbreaker",
                    "role": "Bruiser",
                    "ratio": 0.30,
                    "priority": "Medium",
                    "description": "Tankiness and sustain",
                    "key_boons": ["Might"]
                }
            ],
            GameMode.STRIKES: [
                {
                    "profession": "Guardian",
                    "specialization": "Firebrand",
                    "role": "Support",
                    "ratio": 0.20,
                    "priority": "High",
                    "description": "Quickness and healing",
                    "key_boons": ["Quickness", "Aegis"]
                },
                {
                    "profession": "Revenant",
                    "specialization": "Renegade",
                    "role": "Support",
                    "ratio": 0.20,
                    "priority": "High",
                    "description": "Alacrity and DPS",
                    "key_boons": ["Alacrity", "Might"]
                },
                {
                    "profession": "Warrior",
                    "specialization": "Berserker",
                    "role": "DPS",
                    "ratio": 0.30,
                    "priority": "High",
                    "description": "High DPS",
                    "key_boons": ["Might"]
                },
                {
                    "profession": "Necromancer",
                    "specialization": "Harbinger",
                    "role": "DPS",
                    "ratio": 0.20,
                    "priority": "Medium",
                    "description": "Burst DPS",
                    "key_boons": []
                },
                {
                    "profession": "Mesmer",
                    "specialization": "Virtuoso",
                    "role": "DPS",
                    "ratio": 0.10,
                    "priority": "Low",
                    "description": "Ranged DPS",
                    "key_boons": []
                }
            ]
        }
        
        return ratios.get(game_mode, ratios[GameMode.ZERG])
    
    async def _enhance_with_ml(
        self,
        composition: TeamComposition,
        request_id: str
    ) -> TeamComposition:
        """
        Améliore le score de synergie avec le modèle ML.
        
        Args:
            composition: Composition générée
            request_id: ID de requête
        
        Returns:
            Composition avec score ML
        """
        try:
            from app.learning.models.synergy_model import get_synergy_model
            
            model = get_synergy_model()
            
            # Prédire score ML
            ml_score = model.predict(composition.to_dict())
            
            # Moyenne entre score Mistral et ML (pondération 50/50)
            original_score = composition.synergy_score
            enhanced_score = (original_score + ml_score) / 2.0
            
            composition.synergy_score = enhanced_score
            composition.metadata["ml_score"] = ml_score
            composition.metadata["original_score"] = original_score
            composition.metadata["ml_enhanced"] = True
            
            logger.info(
                "ML enhancement applied",
                extra={
                    "request_id": request_id,
                    "original_score": original_score,
                    "ml_score": ml_score,
                    "enhanced_score": enhanced_score
                }
            )
            
        except Exception as e:
            logger.warning(
                f"ML enhancement failed: {str(e)}",
                extra={"request_id": request_id}
            )
            # Continue without ML enhancement
        
        return composition
    
    async def _save_composition(self, composition: TeamComposition) -> None:
        """
        Sauvegarde une composition pour training futur.
        
        Args:
            composition: Composition à sauvegarder
        """
        try:
            from app.ai.feedback import get_feedback_handler
            
            feedback_handler = get_feedback_handler()
            feedback_handler.save_composition(composition.to_dict())
            
        except Exception as e:
            logger.warning(f"Failed to save composition: {str(e)}")


# Singleton instance
_ai_core_instance: Optional[GW2AICore] = None


async def get_ai_core() -> GW2AICore:
    """
    Récupère ou crée l'instance singleton de AI Core
    
    Returns:
        GW2AICore: Instance du moteur IA
    """
    global _ai_core_instance
    
    if _ai_core_instance is None:
        _ai_core_instance = GW2AICore()
        await _ai_core_instance.initialize()
    
    return _ai_core_instance
