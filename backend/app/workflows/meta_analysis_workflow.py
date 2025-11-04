"""
Meta Analysis Workflow

Workflow d'analyse complète du méta GW2.
Orchestre le Meta Agent et l'intégration API GW2 pour une analyse approfondie.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from app.workflows.base import BaseWorkflow, WorkflowStep
from app.agents.meta_agent import MetaAgent
from app.services.gw2_api_client import GW2APIClient
from app.core.logging import logger


class MetaAnalysisWorkflow(BaseWorkflow):
    """
    Workflow d'analyse de méta.

    Étapes:
    1. Collecte des données de jeu via API GW2
    2. Analyse du méta actuel
    3. Détection des tendances
    4. Génération de recommandations
    5. Création de rapport d'analyse

    Example:
        ```python
        workflow = MetaAnalysisWorkflow()
        result = await workflow.run({
            "game_mode": "zerg",
            "profession": "Guardian",
            "include_api_data": True
        })
        ```
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le workflow d'analyse de méta.

        Args:
            api_key: Clé API GW2 (optionnel)
        """
        super().__init__(
            name="MetaAnalysisWorkflow", description="Workflow d'analyse complète du méta GW2", version="1.0.0"
        )

        self.meta_agent = MetaAgent()
        self.gw2_client = GW2APIClient(api_key=api_key)

        # Définir les étapes du workflow
        self.workflow_steps = [
            {"name": "collect_game_data", "description": "Collecte des données de jeu via API GW2", "required": False},
            {"name": "analyze_meta", "description": "Analyse du méta actuel", "required": True},
            {"name": "detect_trends", "description": "Détection des tendances", "required": True},
            {"name": "generate_recommendations", "description": "Génération de recommandations", "required": True},
            {"name": "create_report", "description": "Création du rapport d'analyse", "required": True},
        ]
        # Initialiser les steps avec des WorkflowStep
        self.steps = [
            WorkflowStep(name=step["name"], agent_name="MetaAgent", inputs={}, depends_on=[])
            for step in self.workflow_steps
        ]

    async def initialize(self) -> None:
        """Initialise le workflow."""
        logger.info("Initializing Meta Analysis Workflow")
        await self.meta_agent.initialize()
        self._is_initialized = True

    async def _initialize_impl(self) -> None:
        """Initialisation spécifique du workflow."""
        await self.initialize()

    async def define_steps(self, inputs: Dict[str, Any]) -> List[WorkflowStep]:
        """Définit les étapes du workflow (requis par BaseWorkflow)."""
        return self.steps

    async def process_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les résultats (requis par BaseWorkflow)."""
        return step_results

    async def _update_step_status(self, step_name: str, status: str) -> None:
        """Met à jour le statut d'une étape."""
        logger.info(f"Step '{step_name}' status: {status}")

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute le workflow d'analyse de méta.

        Args:
            inputs: Dictionnaire contenant:
                - game_mode (str): Mode de jeu
                - profession (str, optional): Profession à analyser
                - include_api_data (bool, optional): Inclure les données API GW2
                - time_range (int, optional): Période d'analyse en jours
                - current_builds (List[Dict], optional): Builds à analyser

        Returns:
            Dictionnaire contenant le rapport d'analyse complet
        """
        # Validation des inputs
        try:
            await self.validate_inputs(inputs)
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            return {"success": False, "error": str(e), "workflow": self.name}

        game_mode = inputs.get("game_mode")
        profession = inputs.get("profession")
        include_api_data = inputs.get("include_api_data", False)
        time_range = inputs.get("time_range", 30)
        current_builds = inputs.get("current_builds", [])

        logger.info(f"Starting Meta Analysis Workflow for game_mode={game_mode}, " f"profession={profession}")

        workflow_context = {
            "game_mode": game_mode,
            "profession": profession,
            "time_range": time_range,
            "current_builds": current_builds,
        }

        # Étape 1: Collecte des données de jeu (optionnel)
        if include_api_data:
            await self._update_step_status("collect_game_data", "running")

            try:
                game_data = await self._collect_game_data(profession)
                workflow_context["game_data"] = game_data
                await self._update_step_status("collect_game_data", "completed")
                logger.info("Game data collected successfully")
            except Exception as e:
                logger.error(f"Failed to collect game data: {e}")
                await self._update_step_status("collect_game_data", "failed")
                workflow_context["game_data"] = None

        # Étape 2: Analyse du méta
        await self._update_step_status("analyze_meta", "running")

        try:
            meta_analysis = await self.meta_agent.run(
                {
                    "game_mode": game_mode,
                    "profession": profession,
                    "current_builds": current_builds,
                    "time_range": time_range,
                }
            )

            workflow_context["meta_analysis"] = meta_analysis.get("result", {})
            await self._update_step_status("analyze_meta", "completed")
            logger.info("Meta analysis completed")
        except Exception as e:
            logger.error(f"Meta analysis failed: {e}")
            await self._update_step_status("analyze_meta", "failed")
            return {"success": False, "error": f"Meta analysis failed: {str(e)}", "workflow": self.name}

        # Étape 3: Détection des tendances (déjà incluse dans meta_analysis)
        await self._update_step_status("detect_trends", "completed")

        # Étape 4: Génération de recommandations (déjà incluse dans meta_analysis)
        await self._update_step_status("generate_recommendations", "completed")

        # Étape 5: Création du rapport
        await self._update_step_status("create_report", "running")

        try:
            report = await self._create_analysis_report(workflow_context)
            await self._update_step_status("create_report", "completed")
            logger.info("Analysis report created")
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            await self._update_step_status("create_report", "failed")
            return {"success": False, "error": f"Report creation failed: {str(e)}", "workflow": self.name}

        return {
            "success": True,
            "workflow": self.name,
            "report": report,
            "execution_timestamp": datetime.utcnow().isoformat(),
        }

    async def _collect_game_data(self, profession: Optional[str] = None) -> Dict[str, Any]:
        """
        Collecte les données de jeu via l'API GW2.

        Args:
            profession: Profession à récupérer (optionnel)

        Returns:
            Données de jeu collectées
        """
        logger.info("Collecting game data from GW2 API")

        data = {}

        try:
            if profession:
                # Récupérer uniquement la profession demandée
                profession_data = await self.gw2_client.get_profession(profession)
                data["profession"] = profession_data

                # Récupérer les spécialisations de la profession
                if "specializations" in profession_data:
                    spec_ids = profession_data["specializations"]
                    specializations = await self.gw2_client.get_specializations(spec_ids)
                    data["specializations"] = specializations
            else:
                # Récupérer toutes les professions
                professions = await self.gw2_client.get_all_professions_details()
                data["professions"] = professions

            data["success"] = True

        except Exception as e:
            logger.error(f"Failed to collect game data: {e}")
            data["success"] = False
            data["error"] = str(e)

        return data

    async def _create_analysis_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée le rapport d'analyse complet.

        Args:
            context: Contexte du workflow

        Returns:
            Rapport d'analyse
        """
        logger.info("Creating meta analysis report")

        meta_analysis = context.get("meta_analysis", {})
        game_data = context.get("game_data")

        report = {
            "title": "Meta Analysis Report",
            "game_mode": context.get("game_mode"),
            "profession": context.get("profession"),
            "analysis_period": f"{context.get('time_range', 30)} days",
            "generated_at": datetime.utcnow().isoformat(),
            # Résumé exécutif
            "executive_summary": self._create_executive_summary(meta_analysis),
            # État du méta
            "meta_snapshot": meta_analysis.get("meta_snapshot", {}),
            # Tendances
            "trends": meta_analysis.get("trends", []),
            # Scores de viabilité
            "viability_scores": meta_analysis.get("viability_scores", {}),
            # Recommandations
            "recommendations": meta_analysis.get("recommendations", []),
            # Prédictions
            "predictions": meta_analysis.get("predictions", {}),
            # Données de jeu (si disponibles)
            "game_data_included": game_data is not None,
        }

        if game_data:
            report["game_data_summary"] = self._summarize_game_data(game_data)

        return report

    def _create_executive_summary(self, meta_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée le résumé exécutif de l'analyse.

        Args:
            meta_analysis: Résultats de l'analyse de méta

        Returns:
            Résumé exécutif
        """
        trends = meta_analysis.get("trends", [])
        recommendations = meta_analysis.get("recommendations", [])
        viability_scores = meta_analysis.get("viability_scores", {})

        # Calculer les statistiques
        avg_viability = sum(viability_scores.values()) / len(viability_scores) if viability_scores else 0

        high_priority_recs = [r for r in recommendations if r.get("priority") == "high"]

        strong_trends = [t for t in trends if t.get("confidence", 0) > 0.7]

        return {
            "total_trends_detected": len(trends),
            "strong_trends": len(strong_trends),
            "average_build_viability": round(avg_viability, 2),
            "total_recommendations": len(recommendations),
            "high_priority_recommendations": len(high_priority_recs),
            "meta_stability": self._assess_meta_stability(trends),
            "key_insights": self._extract_key_insights(trends, recommendations, viability_scores),
        }

    def _assess_meta_stability(self, trends: List[Dict[str, Any]]) -> str:
        """
        Évalue la stabilité du méta.

        Args:
            trends: Liste des tendances

        Returns:
            Niveau de stabilité (stable, shifting, volatile)
        """
        if not trends:
            return "stable"

        strong_trends = [t for t in trends if t.get("change_percentage", 0) > 0.2]

        if len(strong_trends) >= 3:
            return "volatile"
        elif len(strong_trends) >= 1:
            return "shifting"
        else:
            return "stable"

    def _extract_key_insights(
        self, trends: List[Dict[str, Any]], recommendations: List[Dict[str, Any]], viability_scores: Dict[str, float]
    ) -> List[str]:
        """
        Extrait les insights clés de l'analyse.

        Args:
            trends: Tendances détectées
            recommendations: Recommandations
            viability_scores: Scores de viabilité

        Returns:
            Liste d'insights
        """
        insights = []

        # Insight sur les tendances
        if trends:
            top_trend = max(trends, key=lambda t: t.get("confidence", 0))
            insights.append(f"Tendance principale: {top_trend.get('description', 'N/A')}")

        # Insight sur la viabilité
        if viability_scores:
            low_viability_count = sum(1 for score in viability_scores.values() if score < 0.5)
            if low_viability_count > 0:
                insights.append(f"{low_viability_count} builds nécessitent une optimisation")

        # Insight sur les recommandations
        high_priority = [r for r in recommendations if r.get("priority") == "high"]
        if high_priority:
            insights.append(f"{len(high_priority)} actions prioritaires recommandées")

        return insights

    def _summarize_game_data(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Résume les données de jeu collectées.

        Args:
            game_data: Données de jeu

        Returns:
            Résumé des données
        """
        summary = {
            "data_collected": game_data.get("success", False),
            "profession_data": "profession" in game_data,
            "specializations_count": len(game_data.get("specializations", [])),
            "professions_count": len(game_data.get("professions", [])),
        }

        return summary

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Valide les entrées du workflow."""
        if "game_mode" not in inputs:
            raise ValueError("game_mode is required")

        valid_modes = ["zerg", "raid_guild", "roaming"]
        if inputs["game_mode"] not in valid_modes:
            raise ValueError(f"Invalid game_mode. Must be one of: {', '.join(valid_modes)}")

    async def cleanup(self) -> None:
        """Nettoie les ressources du workflow."""
        await self._cleanup_impl()
        self._is_initialized = False

    async def _cleanup_impl(self) -> None:
        """Nettoyage spécifique du workflow."""
        logger.info("Cleaning up Meta Analysis Workflow")
        await self.meta_agent.cleanup()
        self.gw2_client.clear_cache()
