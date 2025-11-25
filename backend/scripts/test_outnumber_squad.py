#!/usr/bin/env python
"""
Test en condition réelle : Groupe de 5 pour Outnumber en WvW.

Objectif : Créer le groupe de 5 le plus optimisé possible pour faire
de l'outnumber (combattre en infériorité numérique).

Stratégie WvW Outnumber:
- High burst damage
- High mobility
- Self-sustain
- Stealth/Disengage
- Small-scale synergy (pas besoin de boon bot)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.build_equipment_optimizer import get_build_optimizer
from app.engine.core.constants import ARMOR_HEAVY
from app.core.logging import logger


# ==================== COMPOSITIONS META OUTNUMBER ====================

OUTNUMBER_COMP = {
    "name": "Havoc Squad - Outnumber Specialists",
    "description": "Groupe de 5 pour dominer en infériorité numérique",
    "roles": [
        {
            "profession": "Firebrand (Guardian)",
            "role": "Support DPS",
            "build_type": "Radiant Firebrand",
            "base_stats": {
                "power": 2500,
                "precision": 2100,
                "ferocity": 1500,
                "condition_damage": 0,
                "expertise": 0,
                "concentration": 600,  # Boon support
                "healing_power": 300,
                "toughness": 1200,
                "vitality": 1200,
            },
            "skill_rotation": [
                {"name": "Symbol of Resolution", "damage_coefficient": 0.6},
                {"name": "Sword of Justice", "damage_coefficient": 1.2},
                {"name": "Whirling Wrath", "damage_coefficient": 0.5},  # Multi-hit
            ],
        },
        {
            "profession": "Spellbreaker (Warrior)",
            "role": "DPS Boonstrip",
            "build_type": "Full Berserker Power",
            "base_stats": {
                "power": 2800,
                "precision": 2200,
                "ferocity": 1800,
                "condition_damage": 0,
                "expertise": 0,
                "concentration": 0,
                "healing_power": 0,
                "toughness": 1000,
                "vitality": 1000,
            },
            "skill_rotation": [
                {"name": "Arcing Slice", "damage_coefficient": 1.1},
                {"name": "Whirling Axe", "damage_coefficient": 0.5},  # Multi-hit
                {"name": "Throw Axe", "damage_coefficient": 0.8},
            ],
        },
        {
            "profession": "Deadeye (Thief)",
            "role": "Burst DPS",
            "build_type": "Malicious Deadeye",
            "base_stats": {
                "power": 2900,
                "precision": 2400,
                "ferocity": 2000,
                "condition_damage": 0,
                "expertise": 0,
                "concentration": 0,
                "healing_power": 0,
                "toughness": 900,
                "vitality": 900,
            },
            "skill_rotation": [
                {"name": "Death's Judgment", "damage_coefficient": 2.5},  # Burst
                {"name": "Malicious Backstab", "damage_coefficient": 2.0},
                {"name": "Sniper's Shot", "damage_coefficient": 1.5},
            ],
        },
        {
            "profession": "Holosmith (Engineer)",
            "role": "DPS Sustain",
            "build_type": "Berserker Holosmith",
            "base_stats": {
                "power": 2700,
                "precision": 2150,
                "ferocity": 1700,
                "condition_damage": 0,
                "expertise": 0,
                "concentration": 0,
                "healing_power": 200,
                "toughness": 1100,
                "vitality": 1100,
            },
            "skill_rotation": [
                {"name": "Photon Forge", "damage_coefficient": 1.2},
                {"name": "Corona Burst", "damage_coefficient": 1.5},
                {"name": "Prime Light Beam", "damage_coefficient": 1.8},
            ],
        },
        {
            "profession": "Willbender (Guardian)",
            "role": "Mobility DPS",
            "build_type": "Berserker Willbender",
            "base_stats": {
                "power": 2650,
                "precision": 2150,
                "ferocity": 1600,
                "condition_damage": 0,
                "expertise": 0,
                "concentration": 300,
                "healing_power": 200,
                "toughness": 1150,
                "vitality": 1150,
            },
            "skill_rotation": [
                {"name": "Rushing Justice", "damage_coefficient": 1.3},
                {"name": "Heaven's Palm", "damage_coefficient": 1.1},
                {"name": "Sword of Justice", "damage_coefficient": 1.0},
            ],
        },
    ],
}


async def optimize_squad():
    """Optimise chaque build du squad avec le moteur."""
    
    print("=" * 80)
    print("🎯 HAVOC SQUAD OPTIMIZER - WvW Outnumber (5 players)")
    print("=" * 80)
    print()
    print(f"Composition: {OUTNUMBER_COMP['name']}")
    print(f"Stratégie: {OUTNUMBER_COMP['description']}")
    print()
    
    optimizer = get_build_optimizer()
    
    optimized_squad = []
    
    for i, build in enumerate(OUTNUMBER_COMP["roles"], 1):
        print("-" * 80)
        print(f"{i}. {build['profession']} - {build['role']}")
        print(f"   Build: {build['build_type']}")
        print()
        
        # Déterminer le rôle pour l'optimisation
        if "Support" in build["role"]:
            opt_role = "support"
        elif "Tank" in build["role"]:
            opt_role = "tank"
        else:
            opt_role = "dps"
        
        # Optimiser l'équipement
        result = await optimizer.optimize_build(
            base_stats=build["base_stats"],
            skill_rotation=build["skill_rotation"],
            role=opt_role,
        )
        
        # Afficher les résultats
        print(f"   ✅ Optimized Gear:")
        print(f"      Rune: {result.rune_name}")
        print(f"      Sigils: {', '.join(result.sigil_names)}")
        print(f"      Total Burst: {result.total_damage:.0f}")
        print(f"      DPS Increase: +{result.dps_increase_percent:.1f}%")
        print(f"      Survivability: {result.survivability_score:.2f}")
        print(f"      Overall Score: {result.overall_score:.0f}")
        print()
        print(f"   📊 Stats Breakdown:")
        print(f"      Effective Power: {result.breakdown['effective_power']:.0f}")
        print(f"      Crit Chance: {result.breakdown['crit_chance']*100:.1f}%")
        print(f"      Crit Damage: {result.breakdown['crit_damage']*100:.0f}%")
        print(f"      Damage Mult: ×{result.breakdown['damage_multiplier']:.3f}")
        print()
        
        optimized_squad.append({
            "profession": build["profession"],
            "role": build["role"],
            "gear": {
                "rune": result.rune_name,
                "sigils": result.sigil_names,
            },
            "performance": {
                "burst": result.total_damage,
                "dps_increase": result.dps_increase_percent,
                "survivability": result.survivability_score,
            },
        })
    
    # ==================== SQUAD SUMMARY ====================
    print("=" * 80)
    print("🏆 SQUAD OPTIMIZATION COMPLETE")
    print("=" * 80)
    print()
    
    total_burst = sum(p["performance"]["burst"] for p in optimized_squad)
    avg_dps_increase = sum(p["performance"]["dps_increase"] for p in optimized_squad) / len(optimized_squad)
    avg_survivability = sum(p["performance"]["survivability"] for p in optimized_squad) / len(optimized_squad)
    
    print(f"📊 Squad Performance:")
    print(f"   Total Combined Burst: {total_burst:.0f} damage")
    print(f"   Average DPS Increase: +{avg_dps_increase:.1f}%")
    print(f"   Average Survivability: {avg_survivability:.2f}")
    print()
    
    print("👥 Optimized Roster:")
    for i, player in enumerate(optimized_squad, 1):
        print(f"   {i}. {player['profession']} ({player['role']})")
        print(f"      └─ {player['gear']['rune']} + {', '.join(player['gear']['sigils'])}")
    
    print()
    print("=" * 80)
    print("✅ Ce groupe est maintenant optimisé pour l'outnumber en WvW!")
    print("=" * 80)
    print()
    print("🎮 Stratégie recommandée:")
    print("   1. Deadeye marque la cible (highest threat)")
    print("   2. Spellbreaker strip les boons")
    print("   3. Tout le monde focus burst en même temps")
    print("   4. Firebrand donne Aegis/Stability pour survivre")
    print("   5. Holosmith + Willbender assurent la pression continue")
    print()
    print("💡 Avec ces optimisations, le burst combiné devrait one-shot")
    print("   la plupart des cibles isolées en WvW outnumber.")
    print()


async def main():
    """Point d'entrée principal."""
    try:
        await optimize_squad()
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("🚀 Lancement de l'optimisation du Havoc Squad...")
    print("   Context: WvW Outnumber (5v15+)")
    print("   Boons: 25 Might + Fury (self-sufficient)")
    print("   Target: 25 Vulnerability (focus fire)")
    print()
    
    asyncio.run(main())
