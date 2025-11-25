"""Condition (DoT) damage calculations for Guild Wars 2."""

from typing import Dict, Optional
from .constants import CONDITION_BASE_DAMAGE


def calculate_condition_damage(
    condition_type: str,
    condition_damage_stat: int,
    stacks: int = 1,
    duration: float = 1.0,
    target_has_protection: bool = False,
    target_has_resolution: bool = False,
) -> float:
    """
    Calculate condition damage over time.

    Formula:
    DamagePerTick = (BaseDamage + 0.05 × ConditionDamage) × Stacks
    TotalDamage = DamagePerTick × Duration × ReductionModifiers

    Args:
        condition_type: Type of condition (Burning, Bleeding, etc.)
        condition_damage_stat: Player's Condition Damage stat
        stacks: Number of stacks (for stackable conditions)
        duration: Duration in seconds
        target_has_protection: Whether target has Protection boon (-33% power damage only, not condi)
        target_has_resolution: Whether target has Resolution boon (-50% condi damage)

    Returns:
        Total damage over duration

    Raises:
        ValueError: If condition_type is unknown
    """
    base_dmg = CONDITION_BASE_DAMAGE.get(condition_type)
    if base_dmg is None:
        raise ValueError(f"Unknown condition type: {condition_type}")

    # Calculate damage per tick
    # Formula: (Base + 0.05 * ConditionDamage) * Stacks
    damage_per_tick = (base_dmg + 0.05 * condition_damage_stat) * stacks

    # Apply duration
    total_damage = damage_per_tick * duration

    # Resolution reduces condition damage by 50%
    if target_has_resolution:
        total_damage *= 0.50

    return total_damage


def calculate_condition_duration(
    base_duration: float,
    expertise: int,
    additional_duration_percent: float = 0.0,
    boon_duration_bonus: float = 0.0,  # For boons applied by conditions
) -> float:
    """
    Calculate effective condition duration with modifiers.

    Formula:
    EffectiveDuration = BaseDuration × (1 + Expertise/1500 + AdditionalBonus)

    Args:
        base_duration: Base duration from skill tooltip
        expertise: Player's Expertise stat
        additional_duration_percent: Additional duration from traits/runes (as decimal, e.g., 0.20 for +20%)
        boon_duration_bonus: If this condition applies a boon, this affects its duration

    Returns:
        Effective duration in seconds
    """
    # Expertise provides condi duration bonus
    # 15 Expertise = 1% duration
    duration_bonus_from_expertise = expertise / 1500

    # Total multiplier
    total_mult = 1.0 + duration_bonus_from_expertise + additional_duration_percent + boon_duration_bonus

    return base_duration * total_mult


def calculate_all_condition_damage(
    conditions: Dict[str, dict],
    condition_damage_stat: int,
    expertise: int,
    target_has_resolution: bool = False,
    additional_duration_percent: float = 0.0,
) -> Dict[str, dict]:
    """
    Calculate damage for multiple conditions at once.

    Args:
        conditions: Dictionary mapping condition type to config:
            {
                "Burning": {"stacks": 3, "base_duration": 5.0},
                "Bleeding": {"stacks": 10, "base_duration": 8.0},
                ...
            }
        condition_damage_stat: Player's Condition Damage stat
        expertise: Player's Expertise stat
        target_has_resolution: Whether target has Resolution boon
        additional_duration_percent: Bonus condi duration from traits/gear

    Returns:
        Dictionary with damage breakdown per condition type:
        {
            "Burning": {
                "stacks": 3,
                "base_duration": 5.0,
                "effective_duration": 6.5,
                "total_damage": 2850.0,
                "dps": 438.5
            },
            ...
        }
    """
    results = {}

    for condi_type, config in conditions.items():
        stacks = config.get("stacks", 1)
        base_duration = config.get("base_duration", 1.0)

        # Calculate effective duration
        effective_duration = calculate_condition_duration(
            base_duration=base_duration,
            expertise=expertise,
            additional_duration_percent=additional_duration_percent,
        )

        # Calculate total damage
        total_damage = calculate_condition_damage(
            condition_type=condi_type,
            condition_damage_stat=condition_damage_stat,
            stacks=stacks,
            duration=effective_duration,
            target_has_resolution=target_has_resolution,
        )

        # Calculate DPS
        dps = total_damage / effective_duration if effective_duration > 0 else 0

        results[condi_type] = {
            "stacks": stacks,
            "base_duration": base_duration,
            "effective_duration": effective_duration,
            "total_damage": total_damage,
            "dps": dps,
            "duration_bonus_percent": (effective_duration - base_duration) / base_duration
            if base_duration > 0
            else 0,
        }

    # Calculate total DPS from all conditions
    total_dps = sum(result["dps"] for result in results.values())
    total_damage = sum(result["total_damage"] for result in results.values())

    results["_summary"] = {
        "total_damage": total_damage,
        "total_dps": total_dps,
        "num_conditions": len(conditions),
    }

    return results
