"""
Agent d'Optimisation de Composition

Cet agent optimise une composition d'équipe en suggérant
des modifications pour améliorer les performances.
"""

import httpx
import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.synergy_agent import SynergyAgent
from app.core.config import settings
from app.core.logging import logger


class OptimizerAgent(BaseAgent):
    """
    Agent spécialisé dans l'optimisation de compositions d'équipe
    pour Guild Wars 2 en utilisant le modèle Mistral.

    Cet agent utilise une approche itérative pour proposer
    des améliorations à une composition existante.

    Capabilities:
        - Optimisation de composition
        - Suggestions de remplacements
        - Analyse coût/bénéfice
        - Optimisation multi-objectifs

    Example:
        ```python
        agent = OptimizerAgent()
        result = await agent.execute({
            "current_composition": ["Guardian", "Warrior", "Mesmer"],
            "objectives": ["maximize_boons", "balance_damage"],
            "game_mode": "Raids",
            "max_changes": 2
        })
        print(result["result"]["optimized_composition"])
        ```
    """

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None, timeout: int = 120):
        """
        Initialise l'agent d'optimisation.

        Args:
            model: Nom du modèle Mistral à utiliser
            host: URL de l'hôte Ollama
            timeout: Timeout pour les requêtes HTTP en secondes
        """
        super().__init__(
            name="OptimizerAgent",
            description="Agent d'optimisation de composition d'équipe GW2 utilisant Mistral",
            version="1.0.0",
            capabilities=[
                "composition_optimization",
                "replacement_suggestions",
                "cost_benefit_analysis",
                "multi_objective_optimization",
            ],
        )

        self.model = model or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._synergy_agent: Optional[SynergyAgent] = None

    async def _initialize_impl(self) -> None:
        """Initialise le client HTTP et l'agent de synergie."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self._synergy_agent = SynergyAgent(model=self.model, host=self.host, timeout=self.timeout)
        await self._synergy_agent.initialize()
        logger.info("Optimizer agent initialized with synergy analysis capability")

    async def _cleanup_impl(self) -> None:
        """Ferme le client HTTP et nettoie l'agent de synergie."""
        if self._client:
            await self._client.aclose()
            self._client = None

        if self._synergy_agent:
            await self._synergy_agent.cleanup()
            self._synergy_agent = None

        logger.info("Optimizer agent cleaned up")

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Valide les entrées de l'agent.

        Args:
            inputs: Dictionnaire contenant les paramètres

        Raises:
            ValueError: Si les entrées sont invalides
        """
        await super().validate_inputs(inputs)

        if "current_composition" not in inputs:
            raise ValueError("Missing required field: current_composition")

        composition = inputs["current_composition"]

        if not isinstance(composition, list):
            raise ValueError("current_composition must be a list")

        if len(composition) < 1:
            raise ValueError("Composition must have at least 1 profession")

        # Validation de max_changes
        max_changes = inputs.get("max_changes", 3)
        if max_changes < 1 or max_changes > 10:
            raise ValueError("max_changes must be between 1 and 10")

        # Validation des objectifs
        valid_objectives = [
            "maximize_boons",
            "maximize_damage",
            "maximize_survivability",
            "balance_damage",
            "improve_cc",
            "optimize_synergy",
        ]

        objectives = inputs.get("objectives", [])
        if objectives:
            for obj in objectives:
                if obj not in valid_objectives:
                    raise ValueError(f"Invalid objective '{obj}'. Must be one of: {', '.join(valid_objectives)}")

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise une composition d'équipe.

        Args:
            inputs: Dictionnaire contenant:
                - current_composition (List[str]): Composition actuelle
                - objectives (List[str], optional): Objectifs d'optimisation
                - game_mode (str, optional): Mode de jeu
                - max_changes (int, optional): Nombre max de changements (défaut: 3)
                - preserve_roles (bool, optional): Préserver les rôles existants

        Returns:
            Dictionnaire contenant:
                - optimized_composition (List[str]): Composition optimisée
                - changes (List[Dict]): Liste des changements proposés
                - improvement_score (float): Score d'amélioration
                - rationale (str): Explication des changements
                - before_analysis (Dict): Analyse avant optimisation
                - after_analysis (Dict): Analyse après optimisation

        Raises:
            Exception: Si l'optimisation échoue
        """
        current_composition = inputs["current_composition"]
        objectives = inputs.get("objectives", ["optimize_synergy"])
        game_mode = inputs.get("game_mode", "General")
        max_changes = inputs.get("max_changes", 3)
        preserve_roles = inputs.get("preserve_roles", False)

        # Analyse de la composition actuelle
        logger.info(f"Analyzing current composition: {current_composition}")
        current_analysis = await self._synergy_agent.execute(
            {"professions": current_composition, "game_mode": game_mode}
        )

        if not current_analysis["success"]:
            raise Exception("Failed to analyze current composition")

        # Construction du prompt d'optimisation
        prompt = self._build_optimization_prompt(
            current_composition, current_analysis["result"], objectives, game_mode, max_changes, preserve_roles
        )

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
                        "temperature": 0.8,
                        "top_p": 0.9,
                    },
                },
            )
            response.raise_for_status()

            # Extraction de la réponse
            response_data = response.json()
            raw_response = response_data.get("response", "{}")

            # Parse de la réponse JSON
            optimization_result = json.loads(raw_response)

            # Analyse de la composition optimisée
            optimized_composition = optimization_result.get("optimized_composition", [])

            if optimized_composition:
                logger.info(f"Analyzing optimized composition: {optimized_composition}")
                optimized_analysis = await self._synergy_agent.execute(
                    {"professions": optimized_composition, "game_mode": game_mode}
                )

                if optimized_analysis["success"]:
                    optimization_result["after_analysis"] = optimized_analysis["result"]

                    # Calcul du score d'amélioration
                    current_rating = current_analysis["result"].get("overall_rating", 0)
                    optimized_rating = optimized_analysis["result"].get("overall_rating", 0)
                    optimization_result["improvement_score"] = optimized_rating - current_rating

            # Ajout de l'analyse avant optimisation
            optimization_result["before_analysis"] = current_analysis["result"]

            # Métadonnées
            optimization_result["metadata"] = {
                "model": self.model,
                "objectives": objectives,
                "game_mode": game_mode,
                "max_changes": max_changes,
                "timestamp": response_data.get("created_at"),
            }

            logger.info(
                f"Composition optimization completed with {len(optimization_result.get('changes', []))} changes"
            )

            return optimization_result

        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            raise Exception(f"Failed to communicate with AI service: {str(e)}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise Exception(f"Invalid response from AI service: {str(e)}")

        except KeyError as e:
            logger.error(f"Missing key in AI response: {e}")
            raise Exception(f"Incomplete response from AI service: {str(e)}")

    def _build_optimization_prompt(
        self,
        current_composition: List[str],
        current_analysis: Dict[str, Any],
        objectives: List[str],
        game_mode: str,
        max_changes: int,
        preserve_roles: bool,
    ) -> str:
        """
        Construit le prompt d'optimisation pour Mistral.

        Args:
            current_composition: Composition actuelle
            current_analysis: Analyse de la composition actuelle
            objectives: Objectifs d'optimisation
            game_mode: Mode de jeu
            max_changes: Nombre maximum de changements
            preserve_roles: Préserver les rôles existants

        Returns:
            Prompt formaté pour Mistral
        """
        composition_str = ", ".join(current_composition)
        objectives_str = ", ".join(objectives)

        weaknesses = current_analysis.get("weaknesses", [])
        weaknesses_str = "\n".join([f"- {w}" for w in weaknesses])

        current_rating = current_analysis.get("overall_rating", 0)

        prompt = f"""You are an expert Guild Wars 2 team composition optimizer. Your task is to optimize the following team composition:

**Current Composition**: {composition_str}
**Current Rating**: {current_rating}/10
**Game Mode**: {game_mode}
**Optimization Objectives**: {objectives_str}
**Maximum Changes Allowed**: {max_changes}
**Preserve Roles**: {"Yes" if preserve_roles else "No"}

**Current Weaknesses**:
{weaknesses_str if weaknesses_str else "None identified"}

Please provide an optimized composition in JSON format with the following structure:
{{
    "optimized_composition": [
        "List of professions in the optimized team",
        "Must have the same size as the current composition"
    ],
    "changes": [
        {{
            "position": 0,
            "from": "Original profession",
            "to": "New profession",
            "reason": "Detailed explanation of why this change improves the composition"
        }}
    ],
    "rationale": "A comprehensive explanation of the optimization strategy (2-3 paragraphs)",
    "expected_improvements": [
        "List of specific improvements this optimization will bring",
        "Focus on addressing the identified weaknesses"
    ],
    "trade_offs": [
        "List any potential trade-offs or considerations",
        "Be honest about what might be sacrificed"
    ],
    "alternative_options": [
        "List 1-2 alternative optimization approaches if applicable"
    ]
}}

Guidelines:
1. Make strategic changes that address the identified weaknesses
2. Respect the maximum number of changes allowed
3. Consider profession synergies and role balance
4. Provide clear, actionable rationale for each change
5. Focus on the specified optimization objectives
6. If preserve_roles is true, maintain similar roles (e.g., don't replace a support with pure DPS)

Provide practical, meta-relevant suggestions that will genuinely improve the team's effectiveness."""

        return prompt

    async def optimize_iteratively(
        self, initial_composition: List[str], game_mode: str, target_rating: float = 8.5, max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Optimise une composition de manière itérative jusqu'à atteindre un objectif.

        Args:
            initial_composition: Composition initiale
            game_mode: Mode de jeu
            target_rating: Note cible à atteindre
            max_iterations: Nombre maximum d'itérations

        Returns:
            Dictionnaire contenant l'historique d'optimisation
        """
        current_composition = initial_composition.copy()
        optimization_history = []

        for iteration in range(max_iterations):
            logger.info(f"Optimization iteration {iteration + 1}/{max_iterations}")

            result = await self.execute(
                {
                    "current_composition": current_composition,
                    "game_mode": game_mode,
                    "objectives": ["optimize_synergy"],
                    "max_changes": 2,
                }
            )

            if not result["success"]:
                logger.warning(f"Optimization failed at iteration {iteration + 1}")
                break

            optimization_history.append(
                {"iteration": iteration + 1, "composition": current_composition.copy(), "result": result["result"]}
            )

            # Vérification si l'objectif est atteint
            after_analysis = result["result"].get("after_analysis", {})
            current_rating = after_analysis.get("overall_rating", 0)

            if current_rating >= target_rating:
                logger.info(f"Target rating {target_rating} reached at iteration {iteration + 1}")
                break

            # Mise à jour de la composition pour la prochaine itération
            optimized_comp = result["result"].get("optimized_composition")
            if optimized_comp:
                current_composition = optimized_comp
            else:
                logger.warning("No optimized composition returned, stopping iterations")
                break

        return {
            "initial_composition": initial_composition,
            "final_composition": current_composition,
            "iterations": len(optimization_history),
            "history": optimization_history,
            "target_reached": current_rating >= target_rating if optimization_history else False,
        }
