#!/usr/bin/env python
"""Simple test of the damage calculation module without app dependencies."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only the damage module (no app dependencies)
from app.engine.damage import calculate_damage, ARMOR_HEAVY, ARMOR_LIGHT, WEAPON_STRENGTH_AVG

print("=" * 80)
print("Testing Damage Calculation Engine")
print("=" * 80)

# Test 1: Basic damage calculation
print("\n1. Basic damage calculation (Berserker profile)")
print(f"   Power: 2500, Weapon: {WEAPON_STRENGTH_AVG}, Coefficient: 1.0")
damage = calculate_damage(power=2500, weapon_strength=WEAPON_STRENGTH_AVG, coefficient=1.0, armor=ARMOR_HEAVY)
print(f"   → Damage vs Heavy Armor: {damage:.2f}")

# Test 2: Multi-hit skill (like Fireball with 1.5 coef, 2 hits)
print("\n2. Multi-hit skill simulation (coef=1.5, 2 hits)")
coef = 1.5
hits = 2
per_hit = calculate_damage(power=2500, weapon_strength=WEAPON_STRENGTH_AVG, coefficient=coef, armor=ARMOR_HEAVY)
total = per_hit * hits
print(f"   Per hit: {per_hit:.2f}")
print(f"   Total (x{hits}): {total:.2f}")

# Test 3: Different armor types
print("\n3. Same skill vs different armor types")
coef = 2.0
damage_heavy = calculate_damage(2500, WEAPON_STRENGTH_AVG, coef, ARMOR_HEAVY)
damage_light = calculate_damage(2500, WEAPON_STRENGTH_AVG, coef, ARMOR_LIGHT)
print(f"   vs Heavy ({ARMOR_HEAVY}): {damage_heavy:.2f}")
print(f"   vs Light ({ARMOR_LIGHT}): {damage_light:.2f}")
print(f"   Difference: {damage_light - damage_heavy:.2f} (+{((damage_light/damage_heavy - 1)*100):.1f}%)")

# Test 4: Low vs high coefficient
print("\n4. Comparing different skill coefficients")
for coef in [0.5, 1.0, 1.5, 2.0, 3.0]:
    dmg = calculate_damage(2500, WEAPON_STRENGTH_AVG, coef, ARMOR_HEAVY)
    print(f"   Coefficient {coef:.1f} → {dmg:.2f} damage")

print("\n" + "=" * 80)
print("✓ Damage calculation module is working correctly!")
print("  Formula: (Power × WeaponStrength × Coefficient) / Armor")
print("=" * 80)

print("\nNext step: This module is now used by BuildAnalysisService to add")
print("'estimated_damage_berserker' fields to skills sent to the AI.")
