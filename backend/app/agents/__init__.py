"""
AI Agents Module

Ce module contient les agents IA spécialisés pour différentes tâches :
- Recommandation de builds
- Analyse de synergie d'équipe
- Optimisation de composition
- Apprentissage et adaptation

Chaque agent hérite de BaseAgent et implémente une méthode `run` asynchrone.
"""

from app.agents.base import BaseAgent
from app.agents.recommender_agent import RecommenderAgent
from app.agents.synergy_agent import SynergyAgent
from app.agents.optimizer_agent import OptimizerAgent

__all__ = [
    "BaseAgent",
    "RecommenderAgent",
    "SynergyAgent",
    "OptimizerAgent",
]
