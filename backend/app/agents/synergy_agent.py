"""
Agent d'Analyse de Synergie d'Équipe

Cet agent analyse la composition d'une équipe et identifie
les forces, faiblesses et suggestions d'amélioration.
"""

import httpx
import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.logging import logger


class SynergyAgent(BaseAgent):
    """
    Agent spécialisé dans l'analyse de synergie d'équipe
    pour Guild Wars 2 en utilisant le modèle Mistral.

    Capabilities:
        - Analyse de composition d'équipe
        - Identification des synergies
        - Détection des faiblesses
        - Suggestions d'optimisation

    Example:
        ```python
        agent = SynergyAgent()
        result = await agent.execute({
            "professions": ["Guardian", "Warrior", "Mesmer", "Necromancer", "Ranger"],
            "game_mode": "WvW",
            "squad_size": 5
        })
        print(result["result"]["strengths"])
        ```
    """

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None, timeout: int = 90):
        """
        Initialise l'agent d'analyse de synergie.

        Args:
            model: Nom du modèle Mistral à utiliser
            host: URL de l'hôte Ollama
            timeout: Timeout pour les requêtes HTTP en secondes
        """
        super().__init__(
            name="SynergyAgent",
            description="Agent d'analyse de synergie d'équipe GW2 utilisant Mistral",
            version="1.0.0",
            capabilities=[
                "team_composition_analysis",
                "synergy_detection",
                "weakness_identification",
                "optimization_suggestions",
            ],
        )

        self.model = model or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _initialize_impl(self) -> None:
        """Initialise le client HTTP."""
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

        if "professions" not in inputs:
            raise ValueError("Missing required field: professions")

        professions = inputs["professions"]

        if not isinstance(professions, list):
            raise ValueError("professions must be a list")

        if len(professions) < 2:
            raise ValueError("Team must have at least 2 professions")

        if len(professions) > 50:
            raise ValueError("Team composition can have a maximum of 50 professions")

        # Validation des professions
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

        for profession in professions:
            if profession not in valid_professions:
                raise ValueError(
                    f"Invalid profession '{profession}'. " f"Must be one of: {', '.join(valid_professions)}"
                )

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse la synergie d'une équipe.

        Args:
            inputs: Dictionnaire contenant:
                - professions (List[str]): Liste des professions
                - game_mode (str, optional): Mode de jeu
                - squad_size (int, optional): Taille de l'escouade
                - context (str, optional): Contexte additionnel

        Returns:
            Dictionnaire contenant:
                - strengths (List[str]): Forces de la composition
                - weaknesses (List[str]): Faiblesses identifiées
                - suggestions (List[str]): Suggestions d'amélioration
                - boon_coverage (Dict): Couverture des boons
                - damage_types (Dict): Types de dégâts
                - overall_rating (float): Note globale (0-10)

        Raises:
            Exception: Si l'analyse échoue
        """
        professions = inputs["professions"]
        game_mode = inputs.get("game_mode", "General")
        squad_size = inputs.get("squad_size", len(professions))
        context = inputs.get("context", "")

        # Construction du prompt
        prompt = self._build_prompt(professions, game_mode, squad_size, context)

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
                "team_size": len(professions),
                "game_mode": game_mode,
                "professions": professions,
                "timestamp": response_data.get("created_at"),
            }

            logger.info(f"Team synergy analysis completed for {len(professions)} professions " f"in {game_mode}")

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

    def _build_prompt(self, professions: List[str], game_mode: str, squad_size: int, context: str) -> str:
        """
        Construit le prompt pour Mistral.

        Args:
            professions: Liste des professions
            game_mode: Mode de jeu
            squad_size: Taille de l'escouade
            context: Contexte additionnel

        Returns:
            Prompt formaté pour Mistral
        """
        profession_counts = {}
        for prof in professions:
            profession_counts[prof] = profession_counts.get(prof, 0) + 1

        composition_summary = ", ".join([f"{count}x {prof}" for prof, count in profession_counts.items()])

        prompt = f"""You are an expert Guild Wars 2 team composition analyst. Analyze the following team composition and provide a comprehensive synergy analysis:

**Team Composition**: {composition_summary}
**Total Size**: {squad_size} players
**Game Mode**: {game_mode}
{f"**Additional Context**: {context}" if context else ""}

Please provide a detailed analysis in JSON format with the following structure:
{{
    "strengths": [
        "List of key strengths (boon coverage, damage types, crowd control, etc.)",
        "Each strength should be specific and actionable"
    ],
    "weaknesses": [
        "List of identified weaknesses (missing boons, vulnerability to conditions, etc.)",
        "Each weakness should be specific"
    ],
    "suggestions": [
        "Specific suggestions to improve the composition",
        "Include profession swaps or build adjustments",
        "Prioritize the most impactful changes"
    ],
    "boon_coverage": {{
        "might": "Coverage level: Excellent/Good/Fair/Poor",
        "fury": "Coverage level",
        "quickness": "Coverage level",
        "alacrity": "Coverage level",
        "protection": "Coverage level",
        "stability": "Coverage level",
        "resistance": "Coverage level",
        "aegis": "Coverage level"
    }},
    "damage_types": {{
        "power_damage": "Coverage level and sources",
        "condition_damage": "Coverage level and sources",
        "burst_potential": "Assessment of burst damage capability"
    }},
    "crowd_control": {{
        "hard_cc": "Assessment of hard CC availability",
        "soft_cc": "Assessment of soft CC availability"
    }},
    "survivability": {{
        "healing": "Assessment of healing capability",
        "barrier": "Assessment of barrier generation",
        "sustain": "Overall sustain rating"
    }},
    "overall_rating": 7.5,
    "summary": "A brief 2-3 sentence summary of the team's overall effectiveness"
}}

Focus on practical, actionable insights that can help optimize the team composition."""

        return prompt

    async def compare_compositions(
        self, composition_a: List[str], composition_b: List[str], game_mode: str = "General"
    ) -> Dict[str, Any]:
        """
        Compare deux compositions d'équipe.

        Args:
            composition_a: Première composition
            composition_b: Deuxième composition
            game_mode: Mode de jeu

        Returns:
            Dictionnaire contenant la comparaison
        """
        # Analyse de la première composition
        result_a = await self.execute({"professions": composition_a, "game_mode": game_mode})

        # Analyse de la deuxième composition
        result_b = await self.execute({"professions": composition_b, "game_mode": game_mode})

        if not result_a["success"] or not result_b["success"]:
            raise Exception("Failed to analyze one or both compositions")

        return {
            "composition_a": {"professions": composition_a, "analysis": result_a["result"]},
            "composition_b": {"professions": composition_b, "analysis": result_b["result"]},
            "comparison": {
                "rating_difference": (
                    result_b["result"].get("overall_rating", 0) - result_a["result"].get("overall_rating", 0)
                ),
                "better_composition": (
                    "B"
                    if result_b["result"].get("overall_rating", 0) > result_a["result"].get("overall_rating", 0)
                    else "A"
                ),
            },
        }
