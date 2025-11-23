"""
AI Agents Module

Ce module contient tous les agents IA utilisés dans le système.
Chaque agent hérite de BaseAgent et implémente une fonctionnalité spécifique.

Les agents disponibles :
- RecommenderAgent : Recommandations de builds
- SynergyAgent : Analyse de synergies d'équipe
- OptimizerAgent : Optimisation de compositions
- MetaAgent : Analyse et adaptation de méta (v1.1.0)
"""

from app.agents.base import BaseAgent
from app.agents.recommender_agent import RecommenderAgent
from app.agents.synergy_agent import SynergyAgent
from app.agents.optimizer_agent import OptimizerAgent
from app.agents.meta_agent import MetaAgent
from app.agents.analyst_agent import AnalystAgent

__all__ = [
    "BaseAgent",
    "RecommenderAgent",
    "SynergyAgent",
    "OptimizerAgent",
    "MetaAgent",
    "AnalystAgent",
]
