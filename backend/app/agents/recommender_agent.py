"""
Agent de Recommandation de Builds

Cet agent utilise Mistral pour générer des recommandations de builds
basées sur la profession, le rôle et le mode de jeu.
"""

import httpx
import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.logging import logger


class RecommenderAgent(BaseAgent):
    """
    Agent spécialisé dans la génération de recommandations de builds
    pour Guild Wars 2 en utilisant le modèle Mistral.

    Capabilities:
        - Recommandation de builds par profession
        - Analyse du rôle dans l'équipe
        - Adaptation au mode de jeu (PvE, PvP, WvW)
        - Suggestions de synergies

    Example:
        ```python
        agent = RecommenderAgent()
        result = await agent.execute({
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW",
            "context": "Focus on boon support"
        })
        print(result["result"]["build_name"])
        ```
    """

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None, timeout: int = 60):
        """
        Initialise l'agent de recommandation.

        Args:
            model: Nom du modèle Mistral à utiliser (par défaut depuis config)
            host: URL de l'hôte Ollama (par défaut depuis config)
            timeout: Timeout pour les requêtes HTTP en secondes
        """
        super().__init__(
            name="RecommenderAgent",
            description="Agent de recommandation de builds GW2 utilisant Mistral",
            version="1.0.0",
            capabilities=["build_recommendation", "profession_analysis", "role_optimization", "synergy_detection"],
        )

        self.model = model or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _initialize_impl(self) -> None:
        """Initialise le client HTTP pour communiquer avec Ollama."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"HTTP client initialized for {self.host}")

    async def _cleanup_impl(self) -> None:
        """Ferme le client HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client closed")

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Valide les entrées de l'agent.

        Args:
            inputs: Dictionnaire contenant les paramètres

        Raises:
            ValueError: Si les entrées sont invalides
        """
        await super().validate_inputs(inputs)

        required_fields = ["profession", "role", "game_mode"]
        missing_fields = [field for field in required_fields if field not in inputs]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validation des professions GW2
        valid_professions = [
            "Guardian",
            "Revenant",
            "Warrior",
            "Engineer",
            "Ranger",
            "Thief",
            "Elementalist",
            "Mesmer",
            "Necromancer",
        ]

        if inputs["profession"] not in valid_professions:
            raise ValueError(f"Invalid profession. Must be one of: {', '.join(valid_professions)}")

        # Validation des rôles
        valid_roles = ["DPS", "Support", "Tank", "Hybrid", "Healer", "Boon"]

        if inputs["role"] not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        # Validation des modes de jeu
        valid_game_modes = ["PvE", "PvP", "WvW", "Raids", "Fractals", "Strikes"]

        if inputs["game_mode"] not in valid_game_modes:
            raise ValueError(f"Invalid game_mode. Must be one of: {', '.join(valid_game_modes)}")

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère une recommandation de build.

        Args:
            inputs: Dictionnaire contenant:
                - profession (str): Profession GW2
                - role (str): Rôle souhaité (DPS, Support, Tank, etc.)
                - game_mode (str): Mode de jeu
                - context (str, optional): Contexte additionnel

        Returns:
            Dictionnaire contenant:
                - build_name (str): Nom du build recommandé
                - description (str): Description du build
                - synergies (List[str]): Liste des synergies clés
                - traits (Dict): Suggestions de traits
                - equipment (Dict): Suggestions d'équipement

        Raises:
            Exception: Si la génération échoue
        """
        profession = inputs["profession"]
        role = inputs["role"]
        game_mode = inputs["game_mode"]
        context = inputs.get("context", "")

        # Construction du prompt pour Mistral
        prompt = self._build_prompt(profession, role, game_mode, context)

        try:
            # Appel à l'API Ollama/Mistral
            response = await self._client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    },
                },
            )
            response.raise_for_status()

            # Extraction de la réponse
            response_data = response.json()
            raw_response = response_data.get("response", "{}")

            # Parse de la réponse JSON
            result = json.loads(raw_response)

            # Enrichissement de la réponse
            result["metadata"] = {
                "model": self.model,
                "profession": profession,
                "role": role,
                "game_mode": game_mode,
                "timestamp": response_data.get("created_at"),
            }

            logger.info(f"Build recommendation generated for {profession} {role} in {game_mode}")

            return result

        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            raise Exception(f"Failed to communicate with AI service: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise Exception(f"Invalid response from AI service: {str(e)}")

        except KeyError as e:
            logger.error(f"Missing key in AI response: {e}")
            raise Exception(f"Incomplete response from AI service: {str(e)}")

    def _build_prompt(self, profession: str, role: str, game_mode: str, context: str) -> str:
        """
        Construit le prompt pour Mistral.

        Args:
            profession: Profession GW2
            role: Rôle souhaité
            game_mode: Mode de jeu
            context: Contexte additionnel

        Returns:
            Prompt formaté pour Mistral
        """
        prompt = f"""You are an expert Guild Wars 2 build advisor. Generate a detailed build recommendation based on the following specifications:

**Profession**: {profession}
**Role**: {role}
**Game Mode**: {game_mode}
{f"**Additional Context**: {context}" if context else ""}

Please provide a comprehensive build recommendation in JSON format with the following structure:
{{
    "build_name": "A catchy and descriptive name for the build",
    "description": "A detailed description of the build's playstyle, strengths, and ideal use cases (2-3 sentences)",
    "synergies": ["List of key boons, conditions, or mechanics this build excels at"],
    "traits": {{
        "line_1": "First trait line name and key traits",
        "line_2": "Second trait line name and key traits",
        "line_3": "Third trait line name and key traits"
    }},
    "equipment": {{
        "armor": "Recommended armor stats (e.g., Berserker's, Diviner's)",
        "weapons": "Recommended weapon sets",
        "trinkets": "Recommended trinket stats",
        "runes": "Recommended rune set",
        "sigils": "Recommended sigils"
    }},
    "skills": {{
        "heal": "Recommended heal skill",
        "utilities": ["Utility skill 1", "Utility skill 2", "Utility skill 3"],
        "elite": "Recommended elite skill"
    }},
    "rotation_tips": "Brief rotation or gameplay tips (2-3 key points)"
}}

Focus on current meta builds and provide practical, actionable recommendations."""

        return prompt

    async def get_build_variants(self, base_inputs: Dict[str, Any], variant_count: int = 3) -> List[Dict[str, Any]]:
        """
        Génère plusieurs variantes d'un build.

        Args:
            base_inputs: Paramètres de base
            variant_count: Nombre de variantes à générer

        Returns:
            Liste de recommandations de builds
        """
        variants = []

        for i in range(variant_count):
            # Modification du contexte pour obtenir des variantes
            variant_inputs = base_inputs.copy()
            variant_inputs["context"] = (
                f"{base_inputs.get('context', '')} " f"Provide variant #{i + 1} with different trait/equipment choices."
            )

            result = await self.execute(variant_inputs)
            if result["success"]:
                variants.append(result["result"])

        return variants
