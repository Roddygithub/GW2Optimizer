"""Legacy damage module - DEPRECATED. Use app.engine.core.damage instead."""

from __future__ import annotations
import warnings

ARMOR_LIGHT: int = 1967
ARMOR_HEAVY: int = 2597
WEAPON_STRENGTH_AVG: int = 1000


def calculate_damage(power: int, weapon_strength: int, coefficient: float, armor: int = ARMOR_HEAVY) -> float:
    """
    Calculate theoretical GW2 strike damage.

    DEPRECATED: Use app.engine.core.damage.calculate_strike_damage instead.
    This function is kept for backward compatibility only.

    Uses the simplified formula:
        damage = (power * weapon_strength * coefficient) / armor
    """
    warnings.warn(
        "calculate_damage is deprecated. Use app.engine.core.damage.calculate_strike_damage instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if armor <= 0:
        raise ValueError("armor must be positive")
    if weapon_strength <= 0:
        raise ValueError("weapon_strength must be positive")
    return (power * weapon_strength * coefficient) / armor
