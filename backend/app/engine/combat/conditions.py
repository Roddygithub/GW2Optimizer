"""Condition (debuff) effects on targets."""

from typing import Dict
from ..modifiers.base import Modifier, ModifierType


# Condition effects as modifiers on the target
CONDITION_DEBUFFS = {
    "Vulnerability": lambda stacks: Modifier(
        name=f"Vulnerability (x{stacks})",
        source="Condition: Vulnerability",
        modifier_type=ModifierType.DAMAGE_MULTIPLIER,
        value=0.01 * min(stacks, 25),  # +1% per stack, max 25
        metadata={"target_debuff": True},
    ),
    "Weakness": Modifier(
        name="Weakness",
        source="Condition: Weakness",
        modifier_type=ModifierType.DAMAGE_MULTIPLIER,
        value=-0.50,  # -50% endurance regen, 50% fumble chance
        metadata={"target_debuff": True, "affects_endurance": True},
    ),
    "Blind": Modifier(
        name="Blind",
        source="Condition: Blind",
        modifier_type=ModifierType.DAMAGE_MULTIPLIER,
        value=-1.0,  # Next attack misses
        metadata={"target_debuff": True, "one_time": True},
    ),
    "Chilled": Modifier(
        name="Chilled",
        source="Condition: Chilled",
        modifier_type=ModifierType.DAMAGE_MULTIPLIER,
        value=-0.66,  # -66% movement speed and skill recharge
        metadata={"target_debuff": True},
    ),
}
