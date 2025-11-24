"""
GW2 Combat Engine - Complete calculation system.

This module provides a comprehensive combat simulation engine for Guild Wars 2,
including damage calculations, condition damage, healing, modifiers, boons, and gear effects.
"""

# Legacy exports for backward compatibility
from .damage import ARMOR_LIGHT, ARMOR_HEAVY, WEAPON_STRENGTH_AVG, calculate_damage

# New engine exports
from .core import *
from .core.attributes import AttributeCalculator
from .modifiers import Modifier, ModifierType, ModifierCondition
from .combat import CombatContext
from .simulation.calculator import BuildCalculator

__all__ = [
    # Legacy
    "ARMOR_LIGHT",
    "ARMOR_HEAVY",
    "WEAPON_STRENGTH_AVG",
    "calculate_damage",
    # Core
    "AttributeCalculator",
    # Modifiers
    "Modifier",
    "ModifierType",
    "ModifierCondition",
    # Combat
    "CombatContext",
    # Calculator
    "BuildCalculator",
]

__version__ = "2.0.0"
