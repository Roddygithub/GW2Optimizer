"""
Base Agent pour tous les agents IA

Ce module définit la classe abstraite BaseAgent qui sert de fondation
pour tous les agents IA du système.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime

from app.core.logging import logger


class BaseAgent(ABC):
    """
    Classe de base abstraite pour tous les agents IA.

    Chaque agent doit implémenter la méthode `run` qui prend un dictionnaire
    d'entrées et retourne un dictionnaire de résultats.

    Attributes:
        name (str): Nom de l'agent
        description (str): Description de l'agent
        version (str): Version de l'agent
        capabilities (List[str]): Liste des capacités de l'agent

    Example:
        ```python
        class MyAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    name="MyAgent",
                    description="Mon agent personnalisé",
                    version="1.0.0"
                )

            async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                # Logique de l'agent
                return {"result": "success"}
        ```
    """

    def __init__(
        self, name: str, description: str = "", version: str = "1.0.0", capabilities: Optional[List[str]] = None
    ):
        """
        Initialise l'agent de base.

        Args:
            name: Nom de l'agent
            description: Description de l'agent
            version: Version de l'agent
            capabilities: Liste des capacités de l'agent
        """
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or []
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """
        Initialise l'agent (connexions, chargement de modèles, etc.).

        Cette méthode est appelée avant la première exécution de l'agent.
        Les sous-classes peuvent la surcharger pour effectuer des initialisations spécifiques.
        """
        if not self._is_initialized:
            logger.info(f"Initializing agent: {self.name} v{self.version}")
            await self._initialize_impl()
            self._is_initialized = True
            logger.info(f"Agent {self.name} initialized successfully")

    async def _initialize_impl(self) -> None:
        """
        Implémentation de l'initialisation spécifique à l'agent.

        Les sous-classes peuvent surcharger cette méthode.
        """
        pass

    @abstractmethod
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute la tâche principale de l'agent.

        Args:
            inputs: Dictionnaire contenant les paramètres d'entrée

        Returns:
            Dictionnaire contenant les résultats de l'exécution

        Raises:
            NotImplementedError: Si la méthode n'est pas implémentée
        """
        pass

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'agent avec gestion des erreurs et logging.

        Args:
            inputs: Dictionnaire contenant les paramètres d'entrée

        Returns:
            Dictionnaire contenant les résultats de l'exécution

        Raises:
            Exception: Si l'exécution échoue
        """
        # Initialisation si nécessaire
        if not self._is_initialized:
            await self.initialize()

        start_time = datetime.now()
        logger.info(f"Executing agent: {self.name} with inputs: {list(inputs.keys())}")

        try:
            # Validation des entrées
            await self.validate_inputs(inputs)

            # Exécution de l'agent
            result = await self.run(inputs)

            # Validation des sorties
            await self.validate_outputs(result)

            # Mise à jour des statistiques
            self.execution_count += 1
            self.last_execution = datetime.now()

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Agent {self.name} executed successfully in {execution_time:.2f}s")

            return {"success": True, "agent": self.name, "execution_time": execution_time, "result": result}

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Agent {self.name} execution failed after {execution_time:.2f}s: {str(e)}", exc_info=True)
            return {"success": False, "agent": self.name, "execution_time": execution_time, "error": str(e)}

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Valide les entrées de l'agent.

        Args:
            inputs: Dictionnaire contenant les paramètres d'entrée

        Raises:
            ValueError: Si les entrées sont invalides
        """
        if not isinstance(inputs, dict):
            raise ValueError("Inputs must be a dictionary")

    async def validate_outputs(self, outputs: Dict[str, Any]) -> None:
        """
        Valide les sorties de l'agent.

        Args:
            outputs: Dictionnaire contenant les résultats

        Raises:
            ValueError: Si les sorties sont invalides
        """
        if not isinstance(outputs, dict):
            raise ValueError("Outputs must be a dictionary")

    def get_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur l'agent.

        Returns:
            Dictionnaire contenant les informations de l'agent
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "is_initialized": self._is_initialized,
        }

    async def cleanup(self) -> None:
        """
        Nettoie les ressources de l'agent.

        Cette méthode est appelée lors de l'arrêt de l'agent.
        Les sous-classes peuvent la surcharger pour effectuer des nettoyages spécifiques.
        """
        logger.info(f"Cleaning up agent: {self.name}")
        await self._cleanup_impl()
        self._is_initialized = False

    async def _cleanup_impl(self) -> None:
        """
        Implémentation du nettoyage spécifique à l'agent.

        Les sous-classes peuvent surcharger cette méthode.
        """
        pass

    def __repr__(self) -> str:
        """Représentation en chaîne de l'agent."""
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}')>"
