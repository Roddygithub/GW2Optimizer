"""
AI Workflows Module

Ce module contient les workflows qui orchestrent plusieurs agents IA
pour accomplir des tâches complexes.

Les workflows disponibles :
- BuildOptimizationWorkflow : Optimisation complète de builds
- TeamAnalysisWorkflow : Analyse approfondie d'équipe
- LearningWorkflow : Apprentissage et adaptation
"""

from app.workflows.base import BaseWorkflow
from app.workflows.build_optimization_workflow import BuildOptimizationWorkflow
from app.workflows.team_analysis_workflow import TeamAnalysisWorkflow
from app.workflows.learning_workflow import LearningWorkflow

__all__ = [
    "BaseWorkflow",
    "BuildOptimizationWorkflow",
    "TeamAnalysisWorkflow",
    "LearningWorkflow",
]
