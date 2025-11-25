"""Modifier system for traits, gear, and combat effects."""

from .base import Modifier, ModifierType, ModifierCondition
from .conditions import (
    TargetHealthCondition,
    TargetHasConditionCheck,
    BoonActiveCondition,
    PlayerHealthCondition,
    DistanceCondition,
    CombinedCondition,
)
from .stacking import ModifierStacker

__all__ = [
    "Modifier",
    "ModifierType",
    "ModifierCondition",
    "TargetHealthCondition",
    "TargetHasConditionCheck",
    "BoonActiveCondition",
    "PlayerHealthCondition",
    "DistanceCondition",
    "CombinedCondition",
    "ModifierStacker",
]
