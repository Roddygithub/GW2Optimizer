"""
Workflow d'Analyse d'Équipe

Ce workflow orchestre l'analyse complète d'une composition d'équipe
avec optimisation et suggestions détaillées.
"""

from typing import Any, Dict, List

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.core.logging import logger


class TeamAnalysisWorkflow(BaseWorkflow):
    """
    Workflow complet d'analyse d'équipe.

    Ce workflow exécute les étapes suivantes :
    1. Analyse de synergie initiale
    2. Identification des points faibles
    3. Génération de suggestions d'optimisation
    4. Comparaison avec une composition optimisée

    Example:
        ```python
        workflow = TeamAnalysisWorkflow()
        result = await workflow.execute(
            inputs={
                "professions": ["Guardian", "Warrior", "Mesmer", "Necromancer", "Ranger"],
                "game_mode": "WvW",
                "optimize": True
            },
            agent_registry=agents
        )
        print(result["result"]["analysis"])
        ```
    """

    def __init__(self):
        """Initialise le workflow d'analyse d'équipe."""
        super().__init__(
            name="TeamAnalysisWorkflow",
            description="Workflow complet d'analyse et d'optimisation d'équipe",
            version="1.0.0",
        )
        # Initialiser les steps par défaut
        self.steps = [WorkflowStep(name="synergy_analysis", agent_name="synergy", inputs={})]

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Valide les entrées du workflow."""
        required_fields = ["professions", "game_mode"]
        missing_fields = [field for field in required_fields if field not in inputs]

        if missing_fields:
            raise ValueError(f"Missing required field: {missing_fields[0]}")

    async def define_steps(self, inputs: Dict[str, Any]) -> List[WorkflowStep]:
        """
        Définit les étapes du workflow en fonction des entrées.

        Args:
            inputs: Paramètres contenant:
                - professions (List[str]): Liste des professions
                - game_mode (str): Mode de jeu
                - optimize (bool, optional): Si True, inclut l'optimisation
                - max_changes (int, optional): Nombre max de changements pour l'optimisation

        Returns:
            Liste des étapes à exécuter
        """
        steps = []

        # Étape 1: Analyse de synergie initiale
        steps.append(
            WorkflowStep(
                name="initial_analysis",
                agent_name="synergy",
                inputs={"professions": inputs["professions"], "game_mode": inputs.get("game_mode", "General")},
            )
        )

        # Étape 2: Optimisation si demandée
        if inputs.get("optimize", False):
            steps.append(
                WorkflowStep(
                    name="optimization",
                    agent_name="optimizer",
                    inputs={
                        "current_composition": inputs["professions"],
                        "game_mode": inputs.get("game_mode", "General"),
                        "objectives": inputs.get("objectives", ["optimize_synergy"]),
                        "max_changes": inputs.get("max_changes", 3),
                    },
                    depends_on=["initial_analysis"],
                )
            )

            # Étape 3: Analyse de la composition optimisée
            # Cette étape sera créée dynamiquement après l'optimisation

        logger.info(f"Defined {len(steps)} steps for TeamAnalysisWorkflow")

        return steps

    async def process_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite les résultats de toutes les étapes.

        Args:
            step_results: Dictionnaire des résultats par nom d'étape

        Returns:
            Résultat final consolidé
        """
        # Récupération de l'analyse initiale
        initial_analysis = step_results.get("initial_analysis", {})

        # Construction du résultat final
        final_result = {
            "current_composition_analysis": {
                "strengths": initial_analysis.get("strengths", []),
                "weaknesses": initial_analysis.get("weaknesses", []),
                "suggestions": initial_analysis.get("suggestions", []),
                "boon_coverage": initial_analysis.get("boon_coverage", {}),
                "damage_types": initial_analysis.get("damage_types", {}),
                "crowd_control": initial_analysis.get("crowd_control", {}),
                "survivability": initial_analysis.get("survivability", {}),
                "overall_rating": initial_analysis.get("overall_rating", 0),
                "summary": initial_analysis.get("summary", ""),
            }
        }

        # Ajout des résultats d'optimisation si disponibles
        optimization_result = step_results.get("optimization")
        if optimization_result:
            final_result["optimization"] = {
                "optimized_composition": optimization_result.get("optimized_composition", []),
                "changes": optimization_result.get("changes", []),
                "improvement_score": optimization_result.get("improvement_score", 0),
                "rationale": optimization_result.get("rationale", ""),
                "expected_improvements": optimization_result.get("expected_improvements", []),
                "trade_offs": optimization_result.get("trade_offs", []),
                "after_analysis": optimization_result.get("after_analysis", {}),
            }

            # Comparaison avant/après
            final_result["comparison"] = self._compare_compositions(
                initial_analysis, optimization_result.get("after_analysis", {})
            )

            # Recommandation finale
            final_result["recommendation"] = self._generate_recommendation(initial_analysis, optimization_result)
        else:
            # Pas d'optimisation, juste des recommandations basées sur l'analyse
            final_result["recommendations"] = self._generate_basic_recommendations(initial_analysis)

        # Insights détaillés
        final_result["insights"] = self._generate_insights(initial_analysis)

        logger.info("Team analysis workflow results processed successfully")

        return final_result

    def _compare_compositions(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare deux analyses de composition.

        Args:
            before: Analyse avant optimisation
            after: Analyse après optimisation

        Returns:
            Dictionnaire de comparaison
        """
        return {
            "rating_improvement": after.get("overall_rating", 0) - before.get("overall_rating", 0),
            "strengths_added": len(after.get("strengths", [])) - len(before.get("strengths", [])),
            "weaknesses_resolved": len(before.get("weaknesses", [])) - len(after.get("weaknesses", [])),
            "boon_coverage_improvements": self._compare_boon_coverage(
                before.get("boon_coverage", {}), after.get("boon_coverage", {})
            ),
        }

    def _compare_boon_coverage(self, before: Dict[str, str], after: Dict[str, str]) -> List[str]:
        """
        Compare la couverture des boons.

        Args:
            before: Couverture avant
            after: Couverture après

        Returns:
            Liste des améliorations
        """
        improvements = []
        coverage_levels = {"Poor": 0, "Fair": 1, "Good": 2, "Excellent": 3}

        for boon, after_level in after.items():
            before_level = before.get(boon, "Poor")

            after_score = coverage_levels.get(after_level.split(":")[0].strip(), 0)
            before_score = coverage_levels.get(before_level.split(":")[0].strip(), 0)

            if after_score > before_score:
                improvements.append(f"{boon}: {before_level} → {after_level}")

        return improvements

    def _generate_recommendation(self, initial_analysis: Dict[str, Any], optimization_result: Dict[str, Any]) -> str:
        """
        Génère une recommandation finale avec optimisation.

        Args:
            initial_analysis: Analyse initiale
            optimization_result: Résultat de l'optimisation

        Returns:
            Recommandation textuelle
        """
        current_rating = initial_analysis.get("overall_rating", 0)
        improvement = optimization_result.get("improvement_score", 0)
        new_rating = current_rating + improvement

        recommendation = f"**Current Team Rating**: {current_rating}/10\n"
        recommendation += f"**Optimized Team Rating**: {new_rating}/10\n"
        recommendation += f"**Improvement**: +{improvement:.1f}\n\n"

        changes = optimization_result.get("changes", [])
        if changes:
            recommendation += "**Recommended Changes**:\n"
            for change in changes:
                recommendation += f"- Position {change.get('position', '?')}: "
                recommendation += f"{change.get('from', '?')} → {change.get('to', '?')}\n"
                recommendation += f"  Reason: {change.get('reason', 'N/A')}\n"

        recommendation += f"\n**Rationale**: {optimization_result.get('rationale', 'N/A')}\n"

        if improvement >= 1.0:
            recommendation += (
                "\n✓ **Strong Recommendation**: These changes will significantly improve your team's effectiveness."
            )
        elif improvement >= 0.5:
            recommendation += "\n⚠ **Moderate Recommendation**: These changes offer noticeable improvements."
        else:
            recommendation += "\n⚠ **Minor Improvements**: Your current composition is already quite good."

        return recommendation

    def _generate_basic_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Génère des recommandations basiques sans optimisation.

        Args:
            analysis: Analyse de la composition

        Returns:
            Liste de recommandations
        """
        recommendations = []

        # Recommandations basées sur les faiblesses
        weaknesses = analysis.get("weaknesses", [])
        for weakness in weaknesses[:5]:  # Top 5 weaknesses
            recommendations.append(f"⚠ Address: {weakness}")

        # Recommandations basées sur les suggestions
        suggestions = analysis.get("suggestions", [])
        for suggestion in suggestions[:3]:  # Top 3 suggestions
            recommendations.append(f"💡 {suggestion}")

        # Recommandations basées sur la couverture des boons
        boon_coverage = analysis.get("boon_coverage", {})
        poor_boons = [boon for boon, level in boon_coverage.items() if "Poor" in level or "Fair" in level]

        if poor_boons:
            recommendations.append(f"⚠ Improve boon coverage for: {', '.join(poor_boons[:3])}")

        return recommendations

    def _generate_insights(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère des insights détaillés sur la composition.

        Args:
            analysis: Analyse de la composition

        Returns:
            Dictionnaire d'insights
        """
        insights = {
            "team_archetype": self._identify_team_archetype(analysis),
            "key_strengths": analysis.get("strengths", [])[:3],
            "critical_weaknesses": analysis.get("weaknesses", [])[:3],
            "priority_improvements": self._identify_priority_improvements(analysis),
        }

        return insights

    def _identify_team_archetype(self, analysis: Dict[str, Any]) -> str:
        """
        Identifie l'archétype de l'équipe.

        Args:
            analysis: Analyse de la composition

        Returns:
            Nom de l'archétype
        """
        strengths = [s.lower() for s in analysis.get("strengths", [])]

        # Analyse des forces pour identifier l'archétype
        if any("boon" in s or "support" in s for s in strengths):
            return "Boon Support Focused"
        elif any("damage" in s or "dps" in s for s in strengths):
            return "Damage Focused"
        elif any("control" in s or "cc" in s for s in strengths):
            return "Control Focused"
        elif any("sustain" in s or "healing" in s for s in strengths):
            return "Sustain Focused"
        else:
            return "Balanced/Hybrid"

    def _identify_priority_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Identifie les améliorations prioritaires.

        Args:
            analysis: Analyse de la composition

        Returns:
            Liste des améliorations prioritaires
        """
        priorities = []

        # Vérifier la couverture des boons critiques
        boon_coverage = analysis.get("boon_coverage", {})
        critical_boons = ["might", "fury", "quickness", "alacrity"]

        for boon in critical_boons:
            level = boon_coverage.get(boon, "Poor")
            if "Poor" in level:
                priorities.append(f"Critical: Improve {boon} coverage")

        # Vérifier les types de dégâts
        damage_types = analysis.get("damage_types", {})
        if "Poor" in damage_types.get("power_damage", "") and "Poor" in damage_types.get("condition_damage", ""):
            priorities.append("Critical: Insufficient damage output")

        # Vérifier la survie
        survivability = analysis.get("survivability", {})
        if "Poor" in survivability.get("healing", ""):
            priorities.append("Important: Add healing support")

        return priorities[:3]  # Top 3 priorities
