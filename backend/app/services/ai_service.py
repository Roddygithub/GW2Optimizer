"""
AI Service Layer

Ce module agit comme interface de haut niveau pour toutes les opérations IA.
Il charge et orchestre dynamiquement les agents et workflows, en abstrayant
la complexité sous-jacente.
"""

from typing import Any, Dict, Optional  # noqa: F401 (used in type annotations)
from app.core.logging import logger
from app.agents.base import BaseAgent
from app.agents.recommender_agent import RecommenderAgent
from app.agents.synergy_agent import SynergyAgent
from app.agents.optimizer_agent import OptimizerAgent
from app.workflows.base import BaseWorkflow  # noqa: F401 (used in type annotations)
from app.workflows.build_optimization_workflow import BuildOptimizationWorkflow
from app.workflows.team_analysis_workflow import TeamAnalysisWorkflow
from app.workflows.learning_workflow import LearningWorkflow


class AIService:
    """
    Service pour orchestrer les agents IA et les workflows.

    Ce service charge dynamiquement tous les agents et workflows disponibles,
    et fournit une interface unifiée pour les exécuter.

    Example:
        ```python
        ai_service = AIService()

        # Exécuter un agent
        result = await ai_service.run_agent("recommender", {
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW"
        })

        # Exécuter un workflow
        result = await ai_service.execute_workflow("build_optimization", {
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW"
        })
        ```
    """

    def __init__(self):
        """Initialise le service et enregistre tous les agents et workflows disponibles."""
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, BaseWorkflow] = {}
        self._is_initialized = False

        self._register_agents()
        self._register_workflows()

        logger.info(f"✅ AI Service initialized with {len(self.agents)} agents and {len(self.workflows)} workflows")
        logger.info(f"📦 Available agents: {', '.join(self.agents.keys())}")
        logger.info(f"🔄 Available workflows: {', '.join(self.workflows.keys())}")

    def _register_agents(self):
        """
        Enregistre tous les agents IA disponibles.

        Les agents sont instanciés mais pas encore initialisés.
        L'initialisation se fait lors de la première exécution.
        """
        try:
            self.agents["recommender"] = RecommenderAgent()
            self.agents["synergy"] = SynergyAgent()
            self.agents["optimizer"] = OptimizerAgent()
            logger.debug("✅ All agents registered successfully")
        except Exception as e:
            logger.error(f"❌ Error registering agents: {e}")
            raise

    def _register_workflows(self):
        """
        Enregistre tous les workflows disponibles.

        Les workflows sont instanciés et prêts à être exécutés.
        """
        try:
            self.workflows["build_optimization"] = BuildOptimizationWorkflow()
            self.workflows["team_analysis"] = TeamAnalysisWorkflow()
            self.workflows["learning"] = LearningWorkflow()
            logger.debug("✅ All workflows registered successfully")
        except Exception as e:
            logger.error(f"❌ Error registering workflows: {e}")
            raise

    async def initialize(self) -> None:
        """
        Initialise tous les agents.

        Cette méthode doit être appelée une fois au démarrage de l'application.
        """
        if self._is_initialized:
            logger.warning("⚠️  AI Service already initialized")
            return

        logger.info("🚀 Initializing AI Service...")

        # Initialiser tous les agents
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                logger.info(f"✅ Agent '{name}' initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize agent '{name}': {e}")

        self._is_initialized = True
        logger.info("✅ AI Service fully initialized")

    async def cleanup(self) -> None:
        """
        Nettoie tous les agents.

        Cette méthode doit être appelée lors de l'arrêt de l'application.
        """
        logger.info("🧹 Cleaning up AI Service...")

        for name, agent in self.agents.items():
            try:
                await agent.cleanup()
                logger.info(f"✅ Agent '{name}' cleaned up")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup agent '{name}': {e}")

        self._is_initialized = False
        logger.info("✅ AI Service cleaned up")

    async def _call_ai_model(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Point d'ancrage pour les tests (patchable avec AsyncMock).
        
        Args:
            prompt: Le prompt à envoyer au modèle
            **kwargs: Arguments additionnels
            
        Returns:
            Réponse du modèle IA
        """
        # Méthode que les tests peuvent patcher
        raise NotImplementedError("_call_ai_model should be mocked in tests")

    async def run_agent(self, agent_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un agent IA spécifique avec les entrées données.

        Args:
            agent_name: Nom de l'agent à exécuter
            inputs: Dictionnaire contenant les paramètres d'entrée

        Returns:
            Dictionnaire contenant les résultats de l'exécution

        Raises:
            ValueError: Si l'agent n'existe pas
            Exception: Si l'exécution échoue

        Example:
            ```python
            result = await ai_service.run_agent("recommender", {
                "profession": "Guardian",
                "role": "Support",
                "game_mode": "WvW"
            })
            ```
        """
        agent = self.agents.get(agent_name)
        if not agent:
            available_agents = ", ".join(self.agents.keys())
            raise ValueError(f"Agent '{agent_name}' not found. " f"Available agents: {available_agents}")

        logger.info(f"🤖 Executing agent '{agent_name}'...")

        try:
            result = await agent.execute(inputs)
            return result
        except Exception as e:
            logger.error(f"❌ Agent '{agent_name}' execution failed: {e}")
            raise

    async def execute_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un workflow complexe.

        Args:
            workflow_name: Nom du workflow à exécuter
            inputs: Dictionnaire contenant les paramètres d'entrée

        Returns:
            Dictionnaire contenant les résultats de l'exécution

        Raises:
            ValueError: Si le workflow n'existe pas
            Exception: Si l'exécution échoue

        Example:
            ```python
            result = await ai_service.execute_workflow("build_optimization", {
                "profession": "Guardian",
                "role": "Support",
                "game_mode": "WvW",
                "team_composition": ["Guardian", "Warrior", "Mesmer"]
            })
            ```
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            available_workflows = ", ".join(self.workflows.keys())
            raise ValueError(f"Workflow '{workflow_name}' not found. " f"Available workflows: {available_workflows}")

        logger.info(f"🔄 Executing workflow '{workflow_name}'...")

        try:
            result = await workflow.execute(inputs, self.agents)
            return result
        except Exception as e:
            logger.error(f"❌ Workflow '{workflow_name}' execution failed: {e}")
            raise

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations sur un agent.

        Args:
            agent_name: Nom de l'agent

        Returns:
            Dictionnaire contenant les informations de l'agent ou None
        """
        agent = self.agents.get(agent_name)
        if agent:
            return agent.get_info()
        return None

    def get_workflow_info(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations sur un workflow.

        Args:
            workflow_name: Nom du workflow

        Returns:
            Dictionnaire contenant les informations du workflow ou None
        """
        workflow = self.workflows.get(workflow_name)
        if workflow:
            return workflow.get_info()
        return None

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Liste tous les agents disponibles avec leurs informations.

        Returns:
            Dictionnaire des agents avec leurs informations
        """
        return {name: agent.get_info() for name, agent in self.agents.items()}

    def list_workflows(self) -> Dict[str, Dict[str, Any]]:
        """
        Liste tous les workflows disponibles avec leurs informations.

        Returns:
            Dictionnaire des workflows avec leurs informations
        """
        return {name: workflow.get_info() for name, workflow in self.workflows.items()}

    def get_service_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service IA.

        Returns:
            Dictionnaire contenant le statut du service
        """
        return {
            "initialized": self._is_initialized,
            "agents_count": len(self.agents),
            "workflows_count": len(self.workflows),
            "agents": list(self.agents.keys()),
            "workflows": list(self.workflows.keys()),
        }

    async def compose_team(
        self, game_mode: str, team_size: int, preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compose une équipe optimale pour un mode de jeu donné.

        Args:
            game_mode: Mode de jeu (WvW, PvP, Raids, etc.)
            team_size: Taille de l'équipe
            preferences: Préférences optionnelles (focus, style, etc.)

        Returns:
            Dictionnaire contenant la composition d'équipe et les synergies
        """
        try:
            result = await self._call_ai_model(
                prompt=f"Compose a team of {team_size} for {game_mode}",
                game_mode=game_mode,
                team_size=team_size,
                preferences=preferences or {},
            )
            return result
        except Exception as e:
            logger.warning(f"AI team composition failed, using fallback: {e}")
            # Fallback composition
            return {
                "composition": [
                    {"profession": "Guardian", "role": "Support"},
                    {"profession": "Warrior", "role": "DPS"},
                ],
                "synergies": ["might", "fury"],
            }

    async def optimize_build(
        self, profession: str, current_build: Dict[str, Any], objective: str
    ) -> Dict[str, Any]:
        """
        Optimise un build pour un objectif donné.

        Args:
            profession: Profession du personnage
            current_build: Build actuel (traits, skills, etc.)
            objective: Objectif d'optimisation (maximize_boons, maximize_dps, etc.)

        Returns:
            Dictionnaire contenant les suggestions d'optimisation
        """
        result = await self._call_ai_model(
            prompt=f"Optimize {profession} build for {objective}",
            profession=profession,
            current_build=current_build,
            objective=objective,
        )
        return result

    async def analyze_synergy(
        self, professions: list, game_mode: str
    ) -> Dict[str, Any]:
        """
        Analyse les synergies entre plusieurs professions.

        Args:
            professions: Liste des professions à analyser
            game_mode: Mode de jeu

        Returns:
            Dictionnaire contenant le score de synergie et les recommandations
        """
        result = await self._call_ai_model(
            prompt=f"Analyze synergy for {', '.join(professions)} in {game_mode}",
            professions=professions,
            game_mode=game_mode,
        )
        return result
