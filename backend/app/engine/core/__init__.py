"""Core combat engine for Guild Wars 2 calculations."""

from .constants import *
from .attributes import AttributeCalculator
from .damage import calculate_strike_damage, calculate_average_damage
from .condition import calculate_condition_damage, calculate_condition_duration
from .healing import calculate_healing

__all__ = [
    # Constants
    "ARMOR_LIGHT",
    "ARMOR_MEDIUM",
    "ARMOR_HEAVY",
    "WEAPON_STRENGTH_AVG",
    "BASE_CRIT_CHANCE",
    "BASE_CRIT_DAMAGE",
    "PRECISION_TO_CRIT",
    "FEROCITY_TO_CRIT_DMG",
    "EXPERTISE_TO_CONDI_DURATION",
    "CONCENTRATION_TO_BOON_DURATION",
    "CONDITION_BASE_DAMAGE",
    # Classes & Functions
    "AttributeCalculator",
    "calculate_strike_damage",
    "calculate_average_damage",
    "calculate_condition_damage",
    "calculate_condition_duration",
    "calculate_healing",
]
