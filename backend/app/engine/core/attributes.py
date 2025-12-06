"""Attribute calculations and conversions for GW2 stats."""

from typing import Dict
from .constants import (
    BASE_CRIT_CHANCE,
    BASE_CRIT_DAMAGE,
    PRECISION_TO_CRIT,
    FEROCITY_TO_CRIT_DMG,
    EXPERTISE_TO_CONDI_DURATION,
    CONCENTRATION_TO_BOON_DURATION,
    VITALITY_TO_HEALTH,
    BASE_HEALTH,
)


class AttributeCalculator:
    """Calculate derived stats from base attributes."""

    @staticmethod
    def calculate_crit_chance(
        precision: int, fury_active: bool = False, base: float = BASE_CRIT_CHANCE
    ) -> float:
        """
        Calculate critical hit chance from Precision stat.

        Args:
            precision: Precision attribute value
            fury_active: Whether Fury boon is active (+20% crit)
            base: Base critical chance (5% default)

        Returns:
            Critical chance as a float (0.0 to 1.0, capped at 100%)
        """
        # PRECISION_TO_CRIT already encodes the 100x factor for conversion
        # (e.g. 21 precision = 1% crit => PRECISION_TO_CRIT = 21 * 100 = 2100),
        # so we only divide once to get the crit chance as a decimal.
        crit_from_precision = precision / PRECISION_TO_CRIT
        fury_bonus = 0.20 if fury_active else 0.0

        total_crit = base + crit_from_precision + fury_bonus
        return min(1.0, total_crit)  # Cap at 100%

    @staticmethod
    def calculate_crit_damage(ferocity: int, base: float = BASE_CRIT_DAMAGE) -> float:
        """
        Calculate critical damage multiplier from Ferocity stat.

        Args:
            ferocity: Ferocity attribute value
            base: Base critical damage multiplier (1.5 = 150%)

        Returns:
            Critical damage multiplier (e.g., 2.2 = 220% damage on crit)
        """
        # FEROCITY_TO_CRIT_DMG already includes the 100x factor
        # (e.g. 15 ferocity = 1% crit damage => FEROCITY_TO_CRIT_DMG = 15 * 100 = 1500),
        # so a single division is enough to obtain the decimal bonus.
        crit_damage_from_ferocity = ferocity / FEROCITY_TO_CRIT_DMG
        return base + crit_damage_from_ferocity

    @staticmethod
    def calculate_condition_duration_bonus(expertise: int) -> float:
        """
        Calculate condition duration bonus from Expertise stat.

        Args:
            expertise: Expertise attribute value

        Returns:
            Condition duration bonus as a decimal (e.g., 0.33 = +33% duration)
        """
        return expertise / EXPERTISE_TO_CONDI_DURATION / 100

    @staticmethod
    def calculate_boon_duration_bonus(concentration: int) -> float:
        """
        Calculate boon duration bonus from Concentration stat.

        Args:
            concentration: Concentration attribute value

        Returns:
            Boon duration bonus as a decimal (e.g., 0.50 = +50% duration)
        """
        return concentration / CONCENTRATION_TO_BOON_DURATION / 100

    @staticmethod
    def calculate_effective_power(base_power: int, might_stacks: int = 0) -> int:
        """
        Calculate effective Power including Might boon stacks.

        Args:
            base_power: Base Power attribute
            might_stacks: Number of Might stacks (max 25)

        Returns:
            Effective Power value
        """
        might_stacks = min(might_stacks, 25)  # Cap at 25 stacks
        return base_power + (might_stacks * 30)

    @staticmethod
    def calculate_effective_condition_damage(
        base_condition_damage: int, might_stacks: int = 0
    ) -> int:
        """
        Calculate effective Condition Damage including Might boon stacks.

        Args:
            base_condition_damage: Base Condition Damage attribute
            might_stacks: Number of Might stacks (max 25)

        Returns:
            Effective Condition Damage value
        """
        might_stacks = min(might_stacks, 25)
        return base_condition_damage + (might_stacks * 30)

    @staticmethod
    def calculate_max_health(base_vitality: int, profession_base: int = BASE_HEALTH) -> int:
        """
        Calculate maximum health from Vitality.

        Args:
            base_vitality: Vitality attribute value
            profession_base: Base health for the profession

        Returns:
            Maximum health value
        """
        return profession_base + (base_vitality * VITALITY_TO_HEALTH)

    @staticmethod
    def calculate_all_derived_stats(
        base_stats: Dict[str, int],
        might_stacks: int = 0,
        fury_active: bool = False,
        additional_crit_chance: float = 0.0,
    ) -> Dict[str, float]:
        """
        Calculate all derived stats from base attributes.

        Args:
            base_stats: Dictionary of base stat values
            might_stacks: Number of active Might stacks
            fury_active: Whether Fury boon is active
            additional_crit_chance: Additional crit chance from traits/modifiers

        Returns:
            Dictionary with all calculated derived stats
        """
        effective_power = AttributeCalculator.calculate_effective_power(
            base_stats.get("power", 0), might_stacks
        )

        effective_condition_damage = AttributeCalculator.calculate_effective_condition_damage(
            base_stats.get("condition_damage", 0), might_stacks
        )

        precision = base_stats.get("precision", 0)
        ferocity = base_stats.get("ferocity", 0)

        crit_chance = AttributeCalculator.calculate_crit_chance(
            precision, fury_active, BASE_CRIT_CHANCE
        )
        crit_chance += additional_crit_chance
        crit_chance = min(1.0, crit_chance)  # Re-cap after additions

        crit_damage = AttributeCalculator.calculate_crit_damage(ferocity)

        condition_duration_bonus = AttributeCalculator.calculate_condition_duration_bonus(
            base_stats.get("expertise", 0)
        )

        boon_duration_bonus = AttributeCalculator.calculate_boon_duration_bonus(
            base_stats.get("concentration", 0)
        )

        max_health = AttributeCalculator.calculate_max_health(
            base_stats.get("vitality", 0), BASE_HEALTH
        )

        return {
            "effective_power": effective_power,
            "effective_condition_damage": effective_condition_damage,
            "crit_chance": crit_chance,
            "crit_damage_multiplier": crit_damage,
            "condition_duration_bonus": condition_duration_bonus,
            "boon_duration_bonus": boon_duration_bonus,
            "max_health": max_health,
            "healing_power": base_stats.get("healing_power", 0),
            "toughness": base_stats.get("toughness", 0),
        }
