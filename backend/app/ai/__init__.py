"""
AI Core Module v4.1.0 - "AI Core Stable"

Centralise toute la logique IA pour GW2Optimizer.
Ce module agit comme cerveau unique du système.

Modules:
    - core: Moteur IA central (composition, analyse, orchestration)
    - composer: Génération compositions d'équipe
    - analyzer: Analyse synergies et performance
    - trainer: Apprentissage ML sur feedback utilisateur
    - feedback: Collecte et traitement feedback
    - context: Veille web et context awareness

Feature Flags:
    - AI_CORE_ENABLED: Active/désactive AI Core (défaut: True)
    - ML_TRAINING_ENABLED: Active training ML (défaut: False en prod)
"""

from app.ai.core import GW2AICore, get_ai_core

__all__ = ["GW2AICore", "get_ai_core"]
__version__ = "4.1.0"
