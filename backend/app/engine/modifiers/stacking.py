"""Logic for stacking modifiers (multiplicative vs additive)."""

from typing import Dict, List, Any
from .base import Modifier, ModifierType


class ModifierStacker:
    """Handle stacking logic for multiple modifiers."""

    @staticmethod
    def stack_flat_stats(modifiers: List[Modifier], context: Dict[str, Any]) -> Dict[str, float]:
        """
        Stack flat stat modifiers additively.

        Args:
            modifiers: List of modifiers
            context: Combat context

        Returns:
            Dictionary mapping stat name to total bonus
        """
        stat_bonuses: Dict[str, float] = {}

        for mod in modifiers:
            if mod.modifier_type != ModifierType.FLAT_STAT:
                continue

            if not mod.is_active(context):
                continue

            stat = mod.target_stat
            if stat:
                effective_value = mod.get_effective_value(context)
                stat_bonuses[stat] = stat_bonuses.get(stat, 0.0) + effective_value

        return stat_bonuses

    @staticmethod
    def stack_percent_stats(modifiers: List[Modifier], context: Dict[str, Any]) -> Dict[str, float]:
        """
        Stack percentage stat modifiers.

        Most percent stat modifiers in GW2 stack additively with each other,
        but multiply the base stat.

        Args:
            modifiers: List of modifiers
            context: Combat context

        Returns:
            Dictionary mapping stat name to total multiplier
        """
        stat_mults: Dict[str, float] = {}

        for mod in modifiers:
            if mod.modifier_type != ModifierType.PERCENT_STAT:
                continue

            if not mod.is_active(context):
                continue

            stat = mod.target_stat
            if stat:
                effective_value = mod.get_effective_value(context)
                # Accumulate additively (e.g., +10% and +15% = +25%)
                stat_mults[stat] = stat_mults.get(stat, 0.0) + effective_value

        # Convert to multipliers (e.g., +25% = 1.25x)
        return {stat: 1.0 + bonus for stat, bonus in stat_mults.items()}

    @staticmethod
    def stack_damage_multipliers(
        modifiers: List[Modifier], context: Dict[str, Any], damage_type: str = "all"
    ) -> float:
        """
        Stack damage multipliers.

        GW2 damage modifiers generally stack multiplicatively, BUT there are
        some exceptions (certain sigils/traits stack additively with each other).

        Args:
            modifiers: List of modifiers
            context: Combat context
            damage_type: Filter by damage type ("all", "strike", "condition")

        Returns:
            Final damage multiplier
        """
        # Separate multiplicative and additive modifiers
        multiplicative_mods = []
        additive_group: Dict[str, List[float]] = {}

        for mod in modifiers:
            # Filter by damage type
            if damage_type == "strike" and mod.modifier_type not in [
                ModifierType.DAMAGE_MULTIPLIER,
                ModifierType.STRIKE_DAMAGE_MULTIPLIER,
            ]:
                continue
            elif damage_type == "condition" and mod.modifier_type not in [
                ModifierType.DAMAGE_MULTIPLIER,
                ModifierType.CONDITION_DAMAGE_MULTIPLIER,
            ]:
                continue
            elif mod.modifier_type not in [
                ModifierType.DAMAGE_MULTIPLIER,
                ModifierType.STRIKE_DAMAGE_MULTIPLIER,
                ModifierType.CONDITION_DAMAGE_MULTIPLIER,
            ]:
                continue

            if not mod.is_active(context):
                continue

            effective_value = mod.get_effective_value(context)

            if mod.is_multiplicative:
                multiplicative_mods.append(1.0 + effective_value)
            else:
                # Group additive modifiers by source type
                source_group = mod.metadata.get("additive_group", "default")
                if source_group not in additive_group:
                    additive_group[source_group] = []
                additive_group[source_group].append(effective_value)

        # Calculate final multiplier
        final_mult = 1.0

        # Apply multiplicative modifiers
        for mult in multiplicative_mods:
            final_mult *= mult

        # Apply additive groups (each group stacks additively, then multiplies)
        for group_values in additive_group.values():
            group_total = sum(group_values)
            final_mult *= 1.0 + group_total

        return final_mult

    @staticmethod
    def stack_all_modifiers(
        modifiers: List[Modifier], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process all modifiers and return a comprehensive summary.

        Args:
            modifiers: List of all active modifiers
            context: Combat context

        Returns:
            Dictionary with:
                - stat_bonuses: Flat stat additions
                - stat_multipliers: Percentage stat boosts
                - damage_multiplier: Overall damage multiplier
                - strike_multiplier: Strike damage multiplier
                - condition_multiplier: Condition damage multiplier
                - crit_chance_bonus: Additional crit chance
                - crit_damage_bonus: Additional crit damage
                - active_modifiers: List of active modifier names
        """
        # Filter active modifiers
        active_mods = [m for m in modifiers if m.is_active(context)]

        # Stack different types
        stat_bonuses = ModifierStacker.stack_flat_stats(active_mods, context)
        stat_multipliers = ModifierStacker.stack_percent_stats(active_mods, context)

        outgoing_mods = [m for m in active_mods if not m.metadata.get("incoming_only")]
        incoming_mods = [m for m in active_mods if m.metadata.get("incoming_only")]

        damage_mult = ModifierStacker.stack_damage_multipliers(outgoing_mods, context, "all")
        strike_mult = ModifierStacker.stack_damage_multipliers(outgoing_mods, context, "strike")
        condition_mult = ModifierStacker.stack_damage_multipliers(outgoing_mods, context, "condition")

        incoming_damage_mult = (
            ModifierStacker.stack_damage_multipliers(incoming_mods, context, "all")
            if incoming_mods
            else 1.0
        )

        # Calculate special bonuses
        crit_chance_bonus = 0.0
        crit_damage_bonus = 0.0

        for mod in active_mods:
            if mod.modifier_type == ModifierType.CRIT_CHANCE:
                crit_chance_bonus += mod.get_effective_value(context)
            elif mod.modifier_type == ModifierType.CRIT_DAMAGE:
                crit_damage_bonus += mod.get_effective_value(context)

        return {
            "stat_bonuses": stat_bonuses,
            "stat_multipliers": stat_multipliers,
            "damage_multiplier": damage_mult,
            "strike_multiplier": strike_mult,
            "condition_multiplier": condition_mult,
            "incoming_damage_multiplier": incoming_damage_mult,
            "crit_chance_bonus": crit_chance_bonus,
            "crit_damage_bonus": crit_damage_bonus,
            "active_modifiers": [m.name for m in active_mods],
            "num_active": len(active_mods),
        }
