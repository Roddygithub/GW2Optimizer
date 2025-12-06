"""Complete build damage calculator using the full engine."""

from typing import Dict, List, Any, Optional
from ..core.damage import calculate_average_damage, calculate_multi_hit_damage
from ..core.condition import calculate_all_condition_damage
from ..core.attributes import AttributeCalculator
from ..combat.context import CombatContext
from ..combat.boons import apply_boon_stats, BOON_MODIFIERS
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
        # Apply boon stat bonuses first (handles Might, etc.)
        stats_with_boons = apply_boon_stats(base_stats, context.player_boons)

        def _scale_modifiers_for_uptime(mods: List[Modifier], uptime: float) -> List[Modifier]:
            if uptime >= 0.999:
                return mods
            factor = max(0.0, min(1.0, float(uptime)))
            scaled: List[Modifier] = []
            for m in mods:
                scaled.append(
                    Modifier(
                        name=m.name,
                        source=m.source,
                        modifier_type=m.modifier_type,
                        value=m.value * factor,
                        condition=m.condition,
                        target_stat=m.target_stat,
                        stacks=m.stacks,
                        max_stacks=m.max_stacks,
                        duration=m.duration,
                        cooldown=m.cooldown,
                        internal_cooldown=m.internal_cooldown,
                        proc_chance=m.proc_chance,
                        is_multiplicative=m.is_multiplicative,
                        metadata=dict(m.metadata) if m.metadata else None,
                    )
                )
            return scaled

        # Convert selected boons into explicit modifiers (Quickness, Protection, ...).
        # We deliberately skip Might and Fury here to avoid double-counting, since
        # their effects are already modeled via stats_with_boons and derived stats.
        boon_mods: List[Modifier] = []
        for boon_name, stacks in context.player_boons.items():
            if boon_name in {"Might", "Fury"}:
                continue
            mod_def = BOON_MODIFIERS.get(boon_name)
            if mod_def is None:
                continue
            uptime = context.get_boon_uptime(boon_name)
            if callable(mod_def):
                try:
                    raw_mods = mod_def(stacks)  # type: ignore[arg-type]
                except TypeError:
                    raw_mods = mod_def()  # type: ignore[call-arg]
                boon_mods.extend(_scale_modifiers_for_uptime(list(raw_mods), uptime))
            else:
                boon_mods.extend(_scale_modifiers_for_uptime([mod_def], uptime))

        # Stack all modifiers (gear + boons)
        all_mods = list(modifiers) + boon_mods
        mod_summary = self.stacker.stack_all_modifiers(all_mods, context.to_dict())

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
        derived["incoming_damage_multiplier"] = mod_summary.get("incoming_damage_multiplier", 1.0)

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
                target_has_resolution=context.target_has_boon("Resolution"),
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
