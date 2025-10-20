"""
Base Workflow pour tous les workflows IA

Ce module définit la classe abstraite BaseWorkflow qui sert de fondation
pour tous les workflows d'orchestration d'agents IA.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from app.core.logging import logger


class WorkflowStatus(Enum):
    """États possibles d'un workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """
    Représente une étape dans un workflow.
    
    Attributes:
        name (str): Nom de l'étape
        agent_name (str): Nom de l'agent à exécuter
        inputs (Dict): Paramètres d'entrée
        outputs (Dict): Résultats de l'exécution
        status (WorkflowStatus): État de l'étape
        error (Optional[str]): Message d'erreur si échec
        start_time (Optional[datetime]): Heure de début
        end_time (Optional[datetime]): Heure de fin
    """
    
    def __init__(
        self,
        name: str,
        agent_name: str,
        inputs: Dict[str, Any],
        depends_on: Optional[List[str]] = None
    ):
        """
        Initialise une étape de workflow.
        
        Args:
            name: Nom de l'étape
            agent_name: Nom de l'agent à exécuter
            inputs: Paramètres d'entrée
            depends_on: Liste des noms d'étapes dont celle-ci dépend
        """
        self.name = name
        self.agent_name = agent_name
        self.inputs = inputs
        self.depends_on = depends_on or []
        self.outputs: Dict[str, Any] = {}
        self.status = WorkflowStatus.PENDING
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def start(self) -> None:
        """Marque l'étape comme démarrée."""
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self, outputs: Dict[str, Any]) -> None:
        """
        Marque l'étape comme complétée.
        
        Args:
            outputs: Résultats de l'exécution
        """
        self.status = WorkflowStatus.COMPLETED
        self.outputs = outputs
        self.end_time = datetime.now()
    
    def fail(self, error: str) -> None:
        """
        Marque l'étape comme échouée.
        
        Args:
            error: Message d'erreur
        """
        self.status = WorkflowStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
    
    def get_duration(self) -> Optional[float]:
        """
        Retourne la durée d'exécution en secondes.
        
        Returns:
            Durée en secondes ou None si pas encore terminée
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'étape en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'étape
        """
        return {
            "name": self.name,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "depends_on": self.depends_on,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration()
        }


class BaseWorkflow(ABC):
    """
    Classe de base abstraite pour tous les workflows.
    
    Un workflow orchestre l'exécution de plusieurs agents IA
    pour accomplir une tâche complexe.
    
    Attributes:
        name (str): Nom du workflow
        description (str): Description du workflow
        version (str): Version du workflow
        steps (List[WorkflowStep]): Liste des étapes du workflow
        status (WorkflowStatus): État actuel du workflow
    
    Example:
        ```python
        class MyWorkflow(BaseWorkflow):
            def __init__(self):
                super().__init__(
                    name="MyWorkflow",
                    description="Mon workflow personnalisé",
                    version="1.0.0"
                )
            
            async def define_steps(self, inputs: Dict[str, Any]) -> List[WorkflowStep]:
                return [
                    WorkflowStep("step1", "agent1", {"param": "value"}),
                    WorkflowStep("step2", "agent2", {"param": "value"}, depends_on=["step1"])
                ]
            
            async def process_results(self, step_results: Dict[str, Any]) -> Dict[str, Any]:
                return {"final_result": step_results}
        ```
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0"
    ):
        """
        Initialise le workflow de base.
        
        Args:
            name: Nom du workflow
            description: Description du workflow
            version: Version du workflow
        """
        self.name = name
        self.description = description
        self.version = version
        self.steps: List[WorkflowStep] = []
        self.status = WorkflowStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_count = 0
    
    @abstractmethod
    async def define_steps(self, inputs: Dict[str, Any]) -> List[WorkflowStep]:
        """
        Définit les étapes du workflow en fonction des entrées.
        
        Args:
            inputs: Paramètres d'entrée du workflow
        
        Returns:
            Liste des étapes à exécuter
        
        Raises:
            NotImplementedError: Si la méthode n'est pas implémentée
        """
        pass
    
    @abstractmethod
    async def process_results(
        self,
        step_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Traite les résultats de toutes les étapes.
        
        Args:
            step_results: Dictionnaire des résultats par nom d'étape
        
        Returns:
            Résultat final du workflow
        
        Raises:
            NotImplementedError: Si la méthode n'est pas implémentée
        """
        pass
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        agent_registry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute le workflow complet.
        
        Args:
            inputs: Paramètres d'entrée du workflow
            agent_registry: Registre des agents disponibles
        
        Returns:
            Résultat final du workflow
        
        Raises:
            Exception: Si l'exécution échoue
        """
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
        self.execution_count += 1
        
        logger.info(f"Starting workflow: {self.name} v{self.version}")
        
        try:
            # Définition des étapes
            self.steps = await self.define_steps(inputs)
            logger.info(f"Workflow {self.name} has {len(self.steps)} steps")
            
            # Exécution des étapes
            step_results = await self._execute_steps(agent_registry)
            
            # Traitement des résultats
            final_result = await self.process_results(step_results)
            
            # Workflow complété
            self.status = WorkflowStatus.COMPLETED
            self.end_time = datetime.now()
            
            execution_time = (self.end_time - self.start_time).total_seconds()
            logger.info(
                f"Workflow {self.name} completed successfully in {execution_time:.2f}s"
            )
            
            return {
                "success": True,
                "workflow": self.name,
                "execution_time": execution_time,
                "steps_executed": len(self.steps),
                "result": final_result,
                "steps": [step.to_dict() for step in self.steps]
            }
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.end_time = datetime.now()
            
            execution_time = (self.end_time - self.start_time).total_seconds()
            logger.error(
                f"Workflow {self.name} failed after {execution_time:.2f}s: {str(e)}",
                exc_info=True
            )
            
            return {
                "success": False,
                "workflow": self.name,
                "execution_time": execution_time,
                "error": str(e),
                "steps": [step.to_dict() for step in self.steps]
            }
    
    async def _execute_steps(
        self,
        agent_registry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute toutes les étapes du workflow.
        
        Args:
            agent_registry: Registre des agents disponibles
        
        Returns:
            Dictionnaire des résultats par nom d'étape
        
        Raises:
            Exception: Si une étape échoue
        """
        step_results = {}
        completed_steps = set()
        
        # Exécution des étapes dans l'ordre de dépendance
        while len(completed_steps) < len(self.steps):
            progress_made = False
            
            for step in self.steps:
                # Skip si déjà complétée
                if step.name in completed_steps:
                    continue
                
                # Vérifier si les dépendances sont satisfaites
                if not all(dep in completed_steps for dep in step.depends_on):
                    continue
                
                # Exécuter l'étape
                logger.info(f"Executing step: {step.name} (agent: {step.agent_name})")
                step.start()
                
                try:
                    # Récupérer l'agent
                    agent = agent_registry.get(step.agent_name)
                    if not agent:
                        raise ValueError(f"Agent '{step.agent_name}' not found in registry")
                    
                    # Préparer les entrées avec les résultats des étapes précédentes
                    step_inputs = step.inputs.copy()
                    for dep in step.depends_on:
                        if dep in step_results:
                            step_inputs[f"{dep}_result"] = step_results[dep]
                    
                    # Exécuter l'agent
                    result = await agent.execute(step_inputs)
                    
                    if not result.get("success", False):
                        raise Exception(
                            f"Agent execution failed: {result.get('error', 'Unknown error')}"
                        )
                    
                    # Marquer l'étape comme complétée
                    step.complete(result.get("result", {}))
                    step_results[step.name] = result.get("result", {})
                    completed_steps.add(step.name)
                    progress_made = True
                    
                    logger.info(
                        f"Step {step.name} completed in {step.get_duration():.2f}s"
                    )
                    
                except Exception as e:
                    step.fail(str(e))
                    logger.error(f"Step {step.name} failed: {str(e)}")
                    raise Exception(f"Workflow failed at step '{step.name}': {str(e)}")
            
            # Détection de deadlock
            if not progress_made:
                raise Exception(
                    "Workflow deadlock detected: circular dependencies or missing agents"
                )
        
        return step_results
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur le workflow.
        
        Returns:
            Dictionnaire contenant les informations du workflow
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "steps_count": len(self.steps),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
    
    def __repr__(self) -> str:
        """Représentation en chaîne du workflow."""
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}')>"
