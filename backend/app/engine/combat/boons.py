"""Boon effects and calculations."""

from typing import Dict
from ..modifiers.base import Modifier, ModifierType


# Boon stat bonuses per stack
BOON_STAT_BONUSES = {
    "Might": {"power": 30, "condition_damage": 30},  # per stack, max 25
    "Fury": {},  # Handled as crit chance modifier
    "Vigor": {},  # Endurance regen (not directly stat-related)
    "Swiftness": {},  # Movement speed (not directly stat-related)
    "Quickness": {},  # Attack speed (affects DPS but not direct stats)
    "Alacrity": {},  # Cooldown reduction
    "Protection": {},  # Damage reduction on incoming
    "Aegis": {},  # Block next attack
    "Stability": {},  # CC resist
    "Regeneration": {},  # Healing over time
    "Resistance": {},  # Condition immune
    "Resolution": {},  # Condi damage reduction
}


def apply_boon_stats(base_stats: Dict[str, int], boon_stacks: Dict[str, int]) -> Dict[str, int]:
    """
    Apply boon stat bonuses to base stats.

    Args:
        base_stats: Base stat dictionary
        boon_stacks: Dictionary of boon names to stack counts

    Returns:
        Modified stats with boon bonuses
    """
    stats = base_stats.copy()

    for boon_name, stacks in boon_stacks.items():
        bonuses = BOON_STAT_BONUSES.get(boon_name, {})
        for stat, value_per_stack in bonuses.items():
            stats[stat] = stats.get(stat, 0) + (value_per_stack * stacks)

    return stats


# Boon effects as modifiers
BOON_MODIFIERS = {
    "Might": lambda stacks: [
        Modifier(
            name=f"Might (x{stacks})",
            source="Boon: Might",
            modifier_type=ModifierType.FLAT_STAT,
            value=30 * stacks,
            target_stat="power",
        ),
        Modifier(
            name=f"Might (x{stacks})",
            source="Boon: Might",
            modifier_type=ModifierType.FLAT_STAT,
            value=30 * stacks,
            target_stat="condition_damage",
        ),
    ],
    "Fury": Modifier(
        name="Fury",
        source="Boon: Fury",
        modifier_type=ModifierType.CRIT_CHANCE,
        value=0.20,  # +20% crit chance
    ),
    "Quickness": Modifier(
        name="Quickness",
        source="Boon: Quickness",
        modifier_type=ModifierType.DAMAGE_MULTIPLIER,
        value=0.50,  # Effectively 50% more DPS
        metadata={"affects_dps_only": True},
    ),
    "Protection": Modifier(
        name="Protection",
        source="Boon: Protection",
        modifier_type=ModifierType.DAMAGE_MULTIPLIER,
        value=-0.33,  # -33% incoming damage
        metadata={"incoming_only": True},
    ),
}
