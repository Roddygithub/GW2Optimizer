"""Strike damage calculations for Guild Wars 2."""

from typing import List, Optional
from .constants import ARMOR_HEAVY, BASE_CRIT_DAMAGE


def calculate_strike_damage(
    power: int,
    weapon_strength: int,
    skill_coefficient: float,
    target_armor: int = ARMOR_HEAVY,
    is_critical: bool = False,
    crit_damage_mult: float = BASE_CRIT_DAMAGE,
    vulnerability_stacks: int = 0,
    damage_multipliers: Optional[List[float]] = None,
) -> float:
    """
    Calculate GW2 strike (power-based) damage with full formula.

    Formula:
    Damage = (WeaponStrength × Power × SkillCoef / Armor) 
             × CritMultiplier 
             × VulnerabilityMultiplier
             × OtherMultipliers

    Args:
        power: Player's effective Power stat (including Might)
        weapon_strength: Weapon strength value
        skill_coefficient: Skill damage coefficient from GW2 API
        target_armor: Target's armor value
        is_critical: Whether this is a critical hit
        crit_damage_mult: Critical damage multiplier (1.5 base + ferocity bonus)
        vulnerability_stacks: Number of Vulnerability stacks on target (max 25)
        damage_multipliers: List of additional damage multipliers (e.g., [1.05, 1.10])

    Returns:
        Final damage value

    Raises:
        ValueError: If armor or weapon_strength is <= 0
    """
    if target_armor <= 0:
        raise ValueError("target_armor must be positive")
    if weapon_strength <= 0:
        raise ValueError("weapon_strength must be positive")
    if skill_coefficient < 0:
        raise ValueError("skill_coefficient must be non-negative")

    # Base damage calculation
    base_damage = (weapon_strength * power * skill_coefficient) / target_armor

    # Critical hit multiplier
    if is_critical:
        base_damage *= crit_damage_mult

    # Vulnerability multiplier (+1% damage per stack, max 25)
    vulnerability_stacks = min(vulnerability_stacks, 25)
    if vulnerability_stacks > 0:
        vuln_mult = 1.0 + (vulnerability_stacks * 0.01)
        base_damage *= vuln_mult

    # Apply additional damage multipliers (traits, sigils, runes)
    if damage_multipliers:
        for mult in damage_multipliers:
            base_damage *= mult

    return base_damage


def calculate_average_damage(
    power: int,
    weapon_strength: int,
    skill_coefficient: float,
    crit_chance: float,
    crit_damage_mult: float,
    target_armor: int = ARMOR_HEAVY,
    vulnerability_stacks: int = 0,
    damage_multipliers: Optional[List[float]] = None,
) -> dict:
    """
    Calculate average strike damage considering critical hit chance.

    Args:
        power: Player's effective Power stat
        weapon_strength: Weapon strength value
        skill_coefficient: Skill damage coefficient
        crit_chance: Critical hit chance (0.0 to 1.0)
        crit_damage_mult: Critical damage multiplier
        target_armor: Target's armor value
        vulnerability_stacks: Vulnerability stacks on target
        damage_multipliers: Additional damage multipliers

    Returns:
        Dictionary with:
            - base_damage: Non-critical damage
            - crit_damage: Critical hit damage
            - average_damage: Expected damage value
            - crit_chance: Critical chance used
    """
    # Calculate non-crit damage
    base_dmg = calculate_strike_damage(
        power=power,
        weapon_strength=weapon_strength,
        skill_coefficient=skill_coefficient,
        target_armor=target_armor,
        is_critical=False,
        vulnerability_stacks=vulnerability_stacks,
        damage_multipliers=damage_multipliers,
    )

    # Calculate crit damage
    crit_dmg = calculate_strike_damage(
        power=power,
        weapon_strength=weapon_strength,
        skill_coefficient=skill_coefficient,
        target_armor=target_armor,
        is_critical=True,
        crit_damage_mult=crit_damage_mult,
        vulnerability_stacks=vulnerability_stacks,
        damage_multipliers=damage_multipliers,
    )

    # Calculate average damage (weighted by crit chance)
    crit_chance = max(0.0, min(1.0, crit_chance))  # Clamp between 0 and 1
    avg_dmg = base_dmg * (1 - crit_chance) + crit_dmg * crit_chance

    return {
        "base_damage": base_dmg,
        "crit_damage": crit_dmg,
        "average_damage": avg_dmg,
        "crit_chance": crit_chance,
        "crit_damage_multiplier": crit_damage_mult,
        "damage_increase_from_crit": ((crit_dmg - base_dmg) / base_dmg) if base_dmg > 0 else 0,
    }


def calculate_multi_hit_damage(
    power: int,
    weapon_strength: int,
    hit_coefficients: List[float],
    crit_chance: float,
    crit_damage_mult: float,
    target_armor: int = ARMOR_HEAVY,
    vulnerability_stacks: int = 0,
    damage_multipliers: Optional[List[float]] = None,
) -> dict:
    """
    Calculate total damage for multi-hit skills (e.g., Fireball with direct + explosion).

    Args:
        power: Player's effective Power stat
        weapon_strength: Weapon strength value
        hit_coefficients: List of damage coefficients for each hit
        crit_chance: Critical hit chance
        crit_damage_mult: Critical damage multiplier
        target_armor: Target's armor value
        vulnerability_stacks: Vulnerability stacks on target
        damage_multipliers: Additional damage multipliers

    Returns:
        Dictionary with per-hit and total damage values
    """
    hits = []
    total_avg = 0.0

    for i, coef in enumerate(hit_coefficients, 1):
        hit_result = calculate_average_damage(
            power=power,
            weapon_strength=weapon_strength,
            skill_coefficient=coef,
            crit_chance=crit_chance,
            crit_damage_mult=crit_damage_mult,
            target_armor=target_armor,
            vulnerability_stacks=vulnerability_stacks,
            damage_multipliers=damage_multipliers,
        )

        hits.append(
            {
                "hit_number": i,
                "coefficient": coef,
                "average_damage": hit_result["average_damage"],
                "base_damage": hit_result["base_damage"],
                "crit_damage": hit_result["crit_damage"],
            }
        )

        total_avg += hit_result["average_damage"]

    return {
        "hits": hits,
        "total_hits": len(hit_coefficients),
        "total_average_damage": total_avg,
        "per_hit_breakdown": hits,
    }
