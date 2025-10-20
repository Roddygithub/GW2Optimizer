"""
Workflow d'Optimisation de Build

Ce workflow orchestre plusieurs agents pour optimiser un build complet,
incluant la recommandation, l'analyse et l'optimisation itérative.
"""

from typing import Any, Dict, List, Optional

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.core.logging import logger


class BuildOptimizationWorkflow(BaseWorkflow):
    """
    Workflow complet d'optimisation de build.
    
    Ce workflow exécute les étapes suivantes :
    1. Génération de recommandation initiale
    2. Analyse de synergie (si composition d'équipe fournie)
    3. Optimisation itérative
    4. Génération de variantes
    
    Example:
        ```python
        workflow = BuildOptimizationWorkflow()
        result = await workflow.execute(
            inputs={
                "profession": "Guardian",
                "role": "Support",
                "game_mode": "WvW",
                "team_composition": ["Guardian", "Warrior", "Mesmer"],
                "optimization_iterations": 2
            },
            agent_registry=agents
        )
        print(result["result"]["final_build"])
        ```
    """
    
    def __init__(self):
        """Initialise le workflow d'optimisation de build."""
        super().__init__(
            name="BuildOptimizationWorkflow",
            description="Workflow complet d'optimisation de build avec analyse de synergie",
            version="1.0.0"
        )
        # Initialiser les steps par défaut
        self.steps = [
            WorkflowStep(
                name="build_recommendation",
                agent_name="recommender",
                inputs={}
            ),
            WorkflowStep(
                name="synergy_analysis",
                agent_name="synergy",
                inputs={}
            )
        ]
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Valide les entrées du workflow."""
        required_fields = ["profession", "role", "game_mode"]
        missing_fields = [field for field in required_fields if field not in inputs]
        
        if missing_fields:
            raise ValueError(f"Missing required field: {missing_fields[0]}")
    
    async def define_steps(self, inputs: Dict[str, Any]) -> List[WorkflowStep]:
        """
        Définit les étapes du workflow en fonction des entrées.
        
        Args:
            inputs: Paramètres contenant:
                - profession (str): Profession GW2
                - role (str): Rôle souhaité
                - game_mode (str): Mode de jeu
                - team_composition (List[str], optional): Composition d'équipe
                - optimization_iterations (int, optional): Nombre d'itérations
                - context (str, optional): Contexte additionnel
        
        Returns:
            Liste des étapes à exécuter
        """
        steps = []
        
        # Étape 1: Recommandation initiale de build
        steps.append(WorkflowStep(
            name="initial_recommendation",
            agent_name="recommender",
            inputs={
                "profession": inputs["profession"],
                "role": inputs["role"],
                "game_mode": inputs["game_mode"],
                "context": inputs.get("context", "")
            }
        ))
        
        # Étape 2: Analyse de synergie si composition fournie
        if "team_composition" in inputs and inputs["team_composition"]:
            team_comp = inputs["team_composition"].copy()
            
            # Ajouter la profession du build à la composition si pas déjà présente
            if inputs["profession"] not in team_comp:
                team_comp.append(inputs["profession"])
            
            steps.append(WorkflowStep(
                name="synergy_analysis",
                agent_name="synergy",
                inputs={
                    "professions": team_comp,
                    "game_mode": inputs["game_mode"]
                },
                depends_on=["initial_recommendation"]
            ))
        
        # Étape 3: Génération de variantes
        steps.append(WorkflowStep(
            name="build_variants",
            agent_name="recommender",
            inputs={
                "profession": inputs["profession"],
                "role": inputs["role"],
                "game_mode": inputs["game_mode"],
                "context": f"{inputs.get('context', '')} Generate an alternative variant."
            },
            depends_on=["initial_recommendation"]
        ))
        
        logger.info(f"Defined {len(steps)} steps for BuildOptimizationWorkflow")
        
        return steps
    
    async def process_results(
        self,
        step_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Traite les résultats de toutes les étapes.
        
        Args:
            step_results: Dictionnaire des résultats par nom d'étape
        
        Returns:
            Résultat final consolidé
        """
        # Récupération des résultats
        initial_build = step_results.get("initial_recommendation", {})
        synergy_analysis = step_results.get("synergy_analysis")
        build_variant = step_results.get("build_variants", {})
        
        # Construction du résultat final
        final_result = {
            "primary_build": {
                "name": initial_build.get("build_name", "Unknown Build"),
                "description": initial_build.get("description", ""),
                "synergies": initial_build.get("synergies", []),
                "traits": initial_build.get("traits", {}),
                "equipment": initial_build.get("equipment", {}),
                "skills": initial_build.get("skills", {}),
                "rotation_tips": initial_build.get("rotation_tips", "")
            },
            "alternative_build": {
                "name": build_variant.get("build_name", "Unknown Variant"),
                "description": build_variant.get("description", ""),
                "synergies": build_variant.get("synergies", []),
                "traits": build_variant.get("traits", {}),
                "equipment": build_variant.get("equipment", {})
            }
        }
        
        # Ajout de l'analyse de synergie si disponible
        if synergy_analysis:
            final_result["team_synergy"] = {
                "strengths": synergy_analysis.get("strengths", []),
                "weaknesses": synergy_analysis.get("weaknesses", []),
                "suggestions": synergy_analysis.get("suggestions", []),
                "overall_rating": synergy_analysis.get("overall_rating", 0),
                "boon_coverage": synergy_analysis.get("boon_coverage", {})
            }
            
            # Recommandations basées sur l'analyse de synergie
            final_result["synergy_recommendations"] = self._generate_synergy_recommendations(
                initial_build,
                synergy_analysis
            )
        
        # Comparaison des builds
        final_result["comparison"] = self._compare_builds(
            initial_build,
            build_variant
        )
        
        # Recommandation finale
        final_result["recommendation"] = self._generate_final_recommendation(
            initial_build,
            build_variant,
            synergy_analysis
        )
        
        logger.info("Build optimization workflow results processed successfully")
        
        return final_result
    
    def _generate_synergy_recommendations(
        self,
        build: Dict[str, Any],
        synergy_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Génère des recommandations basées sur l'analyse de synergie.
        
        Args:
            build: Build recommandé
            synergy_analysis: Analyse de synergie
        
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        # Analyse des faiblesses de l'équipe
        weaknesses = synergy_analysis.get("weaknesses", [])
        build_synergies = build.get("synergies", [])
        
        for weakness in weaknesses:
            # Vérifier si le build peut adresser cette faiblesse
            weakness_lower = weakness.lower()
            
            if any(syn.lower() in weakness_lower for syn in build_synergies):
                recommendations.append(
                    f"✓ This build helps address: {weakness}"
                )
            else:
                recommendations.append(
                    f"⚠ Consider adjusting for: {weakness}"
                )
        
        # Suggestions d'amélioration
        suggestions = synergy_analysis.get("suggestions", [])
        for suggestion in suggestions[:3]:  # Top 3 suggestions
            recommendations.append(f"💡 {suggestion}")
        
        return recommendations
    
    def _compare_builds(
        self,
        build_a: Dict[str, Any],
        build_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare deux builds.
        
        Args:
            build_a: Premier build
            build_b: Deuxième build
        
        Returns:
            Dictionnaire de comparaison
        """
        synergies_a = set(build_a.get("synergies", []))
        synergies_b = set(build_b.get("synergies", []))
        
        return {
            "unique_to_primary": list(synergies_a - synergies_b),
            "unique_to_alternative": list(synergies_b - synergies_a),
            "common_synergies": list(synergies_a & synergies_b),
            "primary_focus": self._identify_build_focus(build_a),
            "alternative_focus": self._identify_build_focus(build_b)
        }
    
    def _identify_build_focus(self, build: Dict[str, Any]) -> str:
        """
        Identifie le focus principal d'un build.
        
        Args:
            build: Build à analyser
        
        Returns:
            Description du focus
        """
        synergies = [s.lower() for s in build.get("synergies", [])]
        
        # Analyse des synergies pour identifier le focus
        if any(word in synergies for word in ["quickness", "alacrity", "might"]):
            return "Boon Support"
        elif any(word in synergies for word in ["healing", "regeneration", "barrier"]):
            return "Healing Support"
        elif any(word in synergies for word in ["power", "damage", "burst"]):
            return "Power DPS"
        elif any(word in synergies for word in ["condition", "bleed", "poison", "burn"]):
            return "Condition DPS"
        elif any(word in synergies for word in ["cc", "control", "stun"]):
            return "Crowd Control"
        else:
            return "Hybrid/Balanced"
    
    def _generate_final_recommendation(
        self,
        primary_build: Dict[str, Any],
        alternative_build: Dict[str, Any],
        synergy_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """
        Génère une recommandation finale.
        
        Args:
            primary_build: Build principal
            alternative_build: Build alternatif
            synergy_analysis: Analyse de synergie (optionnel)
        
        Returns:
            Recommandation textuelle
        """
        recommendation = f"**Primary Build**: {primary_build.get('build_name', 'Unknown')}\n"
        recommendation += f"Focus: {self._identify_build_focus(primary_build)}\n\n"
        
        recommendation += f"**Alternative Build**: {alternative_build.get('build_name', 'Unknown')}\n"
        recommendation += f"Focus: {self._identify_build_focus(alternative_build)}\n\n"
        
        if synergy_analysis:
            rating = synergy_analysis.get("overall_rating", 0)
            recommendation += f"**Team Synergy Rating**: {rating}/10\n\n"
            
            if rating >= 8.0:
                recommendation += "✓ Excellent team composition! The recommended build fits well.\n"
            elif rating >= 6.0:
                recommendation += "⚠ Good composition with room for improvement. Consider the suggestions above.\n"
            else:
                recommendation += "⚠ Team composition needs optimization. Review the weaknesses and suggestions.\n"
        
        recommendation += "\n**Recommendation**: Start with the primary build and adjust based on team needs. "
        recommendation += "The alternative build offers a different playstyle if you want more variety."
        
        return recommendation
