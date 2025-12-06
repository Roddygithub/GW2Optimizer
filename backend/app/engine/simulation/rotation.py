from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..combat.context import CombatContext
from ..core.healing import calculate_healing
from ..modifiers.base import Modifier, ModifierType
from .calculator import BuildCalculator


@dataclass
class RotationSkill:
    name: str
    damage_coefficient: float
    cast_time: float = 1.0
    cooldown: float = 8.0
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 0
    heal_coefficient: float = 0.0
    base_heal: float = 0.0


class RotationSimulator:
    def __init__(self) -> None:
        self.calculator = BuildCalculator()

    def simulate_rotation(
        self,
        base_stats: Dict[str, int],
        modifiers: List[Modifier],
        context: CombatContext,
        skills: List[RotationSkill],
        duration: float = 10.0,
        weapon_strength: int = 1000,
        effective_stats: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        if not skills or duration <= 0:
            return {
                "total_damage": 0.0,
                "duration": max(duration, 0.0),
                "dps": 0.0,
                "per_skill": {},
            }

        if effective_stats is None:
            effective_stats = self.calculator.calculate_effective_stats(
                base_stats=base_stats,
                modifiers=modifiers,
                context=context,
            )

        # Calculer les multiplicateurs de soin sortant/entrant à partir des modifiers.
        context_dict = context.to_dict()
        outgoing_heal_bonus = 0.0
        incoming_heal_bonus = 0.0
        for m in modifiers:
            if m.modifier_type == ModifierType.OUTGOING_HEALING:
                outgoing_heal_bonus += m.get_effective_value(context_dict)
            elif m.modifier_type == ModifierType.INCOMING_HEALING:
                incoming_heal_bonus += m.get_effective_value(context_dict)

        outgoing_heal_mult = 1.0 + max(0.0, outgoing_heal_bonus)
        incoming_heal_mult = 1.0 + max(0.0, incoming_heal_bonus)

        num_skills = len(skills)
        next_available: List[float] = [0.0 for _ in range(num_skills)]
        total_damage = 0.0
        total_heal = 0.0
        per_skill: Dict[str, Dict[str, float]] = {}

        current_time = 0.0

        while current_time < duration:
            available_indices = [i for i in range(num_skills) if next_available[i] <= current_time]
            if not available_indices:
                next_time = min(next_available)
                if next_time <= current_time:
                    break
                if next_time >= duration:
                    break
                current_time = next_time
                continue

            best_index = min(
                available_indices,
                key=lambda idx: (skills[idx].priority, idx),
            )
            skill = skills[best_index]

            skill_data: Dict[str, Any] = {
                "name": skill.name,
                "damage_coefficient": skill.damage_coefficient,
            }
            if skill.conditions:
                skill_data["conditions"] = skill.conditions

            result = self.calculator.calculate_skill_damage(
                skill_data=skill_data,
                effective_stats=effective_stats,
                context=context,
                weapon_strength=weapon_strength,
            )
            dmg = float(result.get("total_damage", 0.0))
            total_damage += dmg

            entry = per_skill.setdefault(
                skill.name,
                {"casts": 0.0, "total_damage": 0.0, "total_heal": 0.0},
            )
            entry["casts"] += 1.0
            entry["total_damage"] += dmg

            # Calcul de soin approximatif pour les skills disposant d'un coefficient de heal.
            if skill.heal_coefficient > 0.0 or skill.base_heal > 0.0:
                heal_amount = calculate_healing(
                    base_heal=float(skill.base_heal),
                    healing_power=int(effective_stats.get("healing_power", 0)),
                    coefficient=float(skill.heal_coefficient),
                    outgoing_healing_mult=outgoing_heal_mult,
                    incoming_healing_mult=incoming_heal_mult,
                )
                heal_amount_f = float(heal_amount)
                total_heal += heal_amount_f
                entry["total_heal"] += heal_amount_f

            cast_time = skill.cast_time if skill.cast_time > 0 else 0.1
            cooldown = skill.cooldown if skill.cooldown >= 0 else 0.0
            next_available[best_index] = current_time + cooldown
            current_time += cast_time

        eff_duration = duration if duration > 0 else 1.0
        dps = total_damage / eff_duration
        hps = total_heal / eff_duration if eff_duration > 0 else 0.0

        return {
            "total_damage": total_damage,
            "total_heal": total_heal,
            "duration": duration,
            "dps": dps,
            "hps": hps,
            "per_skill": per_skill,
        }


def get_firebrand_support_wvw_rotation() -> List[Dict[str, Any]]:
    """Rotation canonique simplifiée pour Firebrand support WvW (zerg).

    Cette rotation ne cherche pas à modéliser fidèlement tous les skills,
    mais à capturer le tempo général "Mantra -> Heal -> Stab/Boons" avec
    des coefficients de dégâts modestes (build orienté support/heal).

    Les valeurs de damage_coefficient sont volontairement basses par
    rapport à un DPS pur, car le score global pour les rôles support/boon
    est surtout drivé par les stats de survie/boons, pas par le burst.
    """

    return [
        {
            "name": "FB: Mantra of Liberation",  # Stabilité / quickness, léger heal via traits
            "damage_coefficient": 0.3,
            "cast_time": 0.5,
            "cooldown": 12.0,
            "priority": 0,
            "heal_coefficient": 0.1,
            "base_heal": 600.0,
        },
        {
            "name": "FB: Mantra of Solace",  # Heal + aegis principal
            "damage_coefficient": 0.2,
            "cast_time": 0.5,
            "cooldown": 10.0,
            "priority": 1,
            "heal_coefficient": 0.5,
            "base_heal": 1200.0,
        },
        {
            "name": "FB: Tome of Courage Burst",  # Pulses de soin/protection
            "damage_coefficient": 0.4,
            "cast_time": 1.0,
            "cooldown": 20.0,
            "priority": 2,
            "heal_coefficient": 0.7,
            "base_heal": 2000.0,
        },
        {
            "name": "FB: Mace/Staff Filler",  # Auto / symboles de soutien, heal léger
            "damage_coefficient": 0.6,
            "cast_time": 1.0,
            "cooldown": 1.0,
            "priority": 3,
            "heal_coefficient": 0.05,
            "base_heal": 300.0,
        },
    ]


def get_reaper_power_wvw_rotation() -> List[Dict[str, Any]]:
    """Rotation canonique simplifiée pour Reaper power DPS WvW.

    Cette rotation vise à capturer un cycle de burst en linceul + grands
    coups de greatsword, avec un filler auto-attack. Les coefficients sont
    approximatifs mais permettent au moteur de comparer correctement les
    options d'équipement entre elles.
    """

    return [
        {
            "name": "Reaper: Shroud Burst",
            "damage_coefficient": 3.0,
            "cast_time": 1.0,
            "cooldown": 10.0,
            "priority": 0,
        },
        {
            "name": "Reaper: Gravedigger",
            "damage_coefficient": 2.5,
            "cast_time": 1.5,
            "cooldown": 3.0,
            "priority": 1,
        },
        {
            "name": "Reaper: Greatsword Spin",
            "damage_coefficient": 1.5,
            "cast_time": 1.0,
            "cooldown": 4.0,
            "priority": 2,
        },
        {
            "name": "Reaper: Auto Attack",
            "damage_coefficient": 0.9,
            "cast_time": 1.0,
            "cooldown": 1.0,
            "priority": 3,
        },
    ]
