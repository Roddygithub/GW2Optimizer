"""Complete build damage calculator using the full engine."""

from typing import Dict, List, Any, Optional
from ..core.damage import calculate_average_damage, calculate_multi_hit_damage
from ..core.condition import calculate_all_condition_damage
from ..core.attributes import AttributeCalculator
from ..combat.context import CombatContext
from ..combat.boons import apply_boon_stats
from ..modifiers.base import Modifier
from ..modifiers.stacking import ModifierStacker


class BuildCalculator:
    """Calculate complete build performance with all modifiers."""

    def __init__(self):
        self.attr_calc = AttributeCalculator()
        self.stacker = ModifierStacker()

    def calculate_effective_stats(
        self,
        base_stats: Dict[str, int],
        modifiers: List[Modifier],
        context: CombatContext,
    ) -> Dict[str, float]:
        """
        Calculate effective stats with all modifiers applied.

        Args:
            base_stats: Base stats from gear
            modifiers: All active modifiers (traits, runes, sigils, food)
            context: Combat context with boons

        Returns:
            Dictionary with effective stats
        """
        # Apply boon stat bonuses first
        stats_with_boons = apply_boon_stats(base_stats, context.player_boons)

        # Stack all modifiers
        mod_summary = self.stacker.stack_all_modifiers(modifiers, context.to_dict())

        # Apply flat stat bonuses
        for stat, bonus in mod_summary["stat_bonuses"].items():
            stats_with_boons[stat] = stats_with_boons.get(stat, 0) + int(bonus)

        # Apply percentage stat multipliers
        for stat, mult in mod_summary["stat_multipliers"].items():
            stats_with_boons[stat] = int(stats_with_boons.get(stat, 0) * mult)

        # Calculate derived stats
        fury_active = context.has_boon("Fury")
        derived = self.attr_calc.calculate_all_derived_stats(
            stats_with_boons,
            might_stacks=context.player_boons.get("Might", 0),
            fury_active=fury_active,
            additional_crit_chance=mod_summary["crit_chance_bonus"],
        )

        # Add modifier summary
        derived["damage_multiplier"] = mod_summary["damage_multiplier"]
        derived["strike_multiplier"] = mod_summary["strike_multiplier"]
        derived["condition_multiplier"] = mod_summary["condition_multiplier"]

        return derived

    def calculate_skill_damage(
        self,
        skill_data: Dict[str, Any],
        effective_stats: Dict[str, float],
        context: CombatContext,
        weapon_strength: int = 1000,
    ) -> Dict[str, Any]:
        """
        Calculate total damage for a skill.

        Args:
            skill_data: Skill info with coefficients
            effective_stats: Calculated effective stats
            context: Combat context
            weapon_strength: Weapon strength value

        Returns:
            Complete damage breakdown
        """
        skill_coef = skill_data.get("damage_coefficient", 0)

        # Get damage multipliers
        damage_mults = []
        if effective_stats.get("damage_multiplier"):
            damage_mults.append(effective_stats["damage_multiplier"])
        if effective_stats.get("strike_multiplier"):
            damage_mults.append(effective_stats["strike_multiplier"])

        # Vulnerability on target
        vuln_stacks = context.target_conditions.get("Vulnerability", 0)

        # Calculate strike damage
        strike_result = calculate_average_damage(
            power=int(effective_stats["effective_power"]),
            weapon_strength=weapon_strength,
            skill_coefficient=skill_coef,
            crit_chance=effective_stats["crit_chance"],
            crit_damage_mult=effective_stats["crit_damage_multiplier"],
            target_armor=context.target_armor,
            vulnerability_stacks=vuln_stacks,
            damage_multipliers=damage_mults,
        )

        # Calculate condition damage if skill applies conditions
        condi_result = {}
        if skill_data.get("conditions"):
            condi_result = calculate_all_condition_damage(
                conditions=skill_data["conditions"],
                condition_damage_stat=int(effective_stats["effective_condition_damage"]),
                expertise=int(effective_stats.get("expertise", 0)),
                target_has_resolution=context.target_has_condition("Resolution"),
                additional_duration_percent=effective_stats.get("condition_duration_bonus", 0.0),
            )

        return {
            "skill_name": skill_data.get("name", "Unknown"),
            "strike_damage": strike_result,
            "condition_damage": condi_result,
            "total_damage": strike_result["average_damage"]
            + condi_result.get("_summary", {}).get("total_damage", 0),
            "effective_stats_snapshot": {
                "power": effective_stats["effective_power"],
                "crit_chance": effective_stats["crit_chance"],
                "crit_damage": effective_stats["crit_damage_multiplier"],
                "condition_damage": effective_stats["effective_condition_damage"],
            },
        }
