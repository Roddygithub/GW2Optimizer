#!/usr/bin/env python
"""
Démonstration complète du moteur de calcul GW2.
Montre l'impact des boons, runes, sigils, et vulnerability.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.engine.core.damage import calculate_average_damage
from app.engine.core.attributes import AttributeCalculator
from app.engine.combat.context import CombatContext
from app.engine.modifiers.base import Modifier, ModifierType
from app.engine.modifiers.conditions import TargetHealthCondition
from app.engine.gear.registry import RUNE_REGISTRY, SIGIL_REGISTRY
from app.engine.simulation.calculator import BuildCalculator


def demo_simple_vs_full_build():
    """Démonstration : Simple build vs Build complet avec tout."""
    
    print("=" * 80)
    print("DÉMONSTRATION: Moteur de Calcul GW2 Complet")
    print("=" * 80)
    
    # ==================== Build Simple (sans boons/modifiers) ====================
    print("\n1️⃣  BUILD SIMPLE (gear uniquement)")
    print("-" * 80)
    
    base_stats = {
        "power": 2000,
        "precision": 2100,
        "ferocity": 1200,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 0,
        "healing_power": 0,
        "toughness": 1000,
        "vitality": 1000,
    }
    
    calc = AttributeCalculator()
    simple_derived = calc.calculate_all_derived_stats(base_stats)
    
    print(f"Power: {base_stats['power']}")
    print(f"Crit Chance: {simple_derived['crit_chance']*100:.1f}%")
    print(f"Crit Damage: {simple_derived['crit_damage_multiplier']*100:.0f}%")
    
    # Calcul Fireball (coef 0.8)
    simple_dmg = calculate_average_damage(
        power=base_stats["power"],
        weapon_strength=1000,
        skill_coefficient=0.8,
        crit_chance=simple_derived["crit_chance"],
        crit_damage_mult=simple_derived["crit_damage_multiplier"],
    )
    
    print(f"\n🔥 Fireball damage: {simple_dmg['average_damage']:.0f}")
    
    # ==================== Build Complet (25 Might + Fury + Runes + Sigils) ====================
    print("\n\n2️⃣  BUILD COMPLET (25 Might + Fury + Runes + Sigils + Vuln)")
    print("-" * 80)
    
    # Create combat context with boons
    context = CombatContext.create_default(might_stacks=25, fury=True)
    context.add_condition_to_target("Vulnerability", 25)
    
    # Add modifiers from gear
    modifiers = []
    
    # Scholar Runes
    modifiers.extend(RUNE_REGISTRY["Scholar"]())
    
    # Force Sigil
    modifiers.append(SIGIL_REGISTRY["Force"]())
    
    # Bloodlust Sigil (max stacks)
    modifiers.append(SIGIL_REGISTRY["Bloodlust"](25))
    
    # Food
    modifiers.extend([
        Modifier("Food: Power", "Food", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Food: Ferocity", "Food", ModifierType.FLAT_STAT, 70, target_stat="ferocity"),
    ])
    
    # Use full calculator
    build_calc = BuildCalculator()
    
    effective_stats = build_calc.calculate_effective_stats(
        base_stats=base_stats,
        modifiers=modifiers,
        context=context,
    )
    
    print(f"Effective Power: {effective_stats['effective_power']:.0f} (+{effective_stats['effective_power'] - base_stats['power']:.0f})")
    print(f"Crit Chance: {effective_stats['crit_chance']*100:.1f}% (+{(effective_stats['crit_chance'] - simple_derived['crit_chance'])*100:.1f}%)")
    print(f"Crit Damage: {effective_stats['crit_damage_multiplier']*100:.0f}% (+{(effective_stats['crit_damage_multiplier'] - simple_derived['crit_damage_multiplier'])*100:.0f}%)")
    print(f"Damage Multiplier: ×{effective_stats['damage_multiplier']:.3f}")
    
    # Calculate Fireball with everything
    skill_data = {
        "name": "Fireball",
        "damage_coefficient": 0.8,
    }
    
    full_result = build_calc.calculate_skill_damage(
        skill_data=skill_data,
        effective_stats=effective_stats,
        context=context,
    )
    
    print(f"\n🔥 Fireball damage: {full_result['total_damage']:.0f}")
    print(f"   Base (non-crit): {full_result['strike_damage']['base_damage']:.0f}")
    print(f"   Crit: {full_result['strike_damage']['crit_damage']:.0f}")
    print(f"   Average: {full_result['strike_damage']['average_damage']:.0f}")
    
    # ==================== COMPARAISON ====================
    print("\n\n3️⃣  COMPARAISON FINALE")
    print("=" * 80)
    
    increase = ((full_result['total_damage'] - simple_dmg['average_damage']) / simple_dmg['average_damage']) * 100
    
    print(f"Build Simple:   {simple_dmg['average_damage']:.0f} dégâts")
    print(f"Build Complet:  {full_result['total_damage']:.0f} dégâts")
    print(f"Augmentation:   +{increase:.1f}% 🚀")
    
    print("\n📊 Sources de l'augmentation:")
    print(f"   • Might (25 stacks):      +750 Power")
    print(f"   • Fury:                   +20% Crit Chance")
    print(f"   • Scholar Runes (6/6):    +175 Power, +100 Ferocity, +10% damage")
    print(f"   • Sigil of Force:         +5% damage")
    print(f"   • Sigil of Bloodlust:     +250 Power")
    print(f"   • Food:                   +100 Power, +70 Ferocity")
    print(f"   • 25 Vulnerability:       +25% damage")
    
    print("\n✅ Le moteur prend en compte TOUS ces éléments automatiquement!")
    print("=" * 80)


if __name__ == "__main__":
    demo_simple_vs_full_build()
