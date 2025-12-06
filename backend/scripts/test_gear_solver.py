#!/usr/bin/env python
from __future__ import annotations

"""Minimal integration test for GearOptimizationService.

Usage (from backend/ directory):

    poetry run python scripts/test_gear_solver.py

This script does *not* run as a formal unit test; it's a quick judge
for the greedy armor solver behaviour on a simple DPS + HP constraint
scenario.
"""

from typing import Dict

from app.engine.core.attributes import AttributeCalculator
from app.engine.core.constants import BASE_STATS
from app.services.gear_optimization_service import get_gear_optimization_service


def _merge_base_and_gear(base: Dict[str, int], gear: Dict[str, int]) -> Dict[str, int]:
    all_keys = set(base.keys()) | set(gear.keys())
    merged: Dict[str, int] = {}
    for k in all_keys:
        merged[k] = int(base.get(k, 0)) + int(gear.get(k, 0))
    return merged


def main() -> None:
    service = get_gear_optimization_service()

    # Scenario: WvW DPS roaming-like with a desire for ~20k HP.
    role = "dps"
    profession = "Guardian"  # just a label for now
    specialization = "Firebrand"  # not used yet by the solver
    mode = "wvw_roam"
    experience = "intermediate"

    print("=== GearOptimizationService greedy armor test ===")
    print(f"Role: {role}, mode: {mode}, experience: {experience}")

    # Run the greedy solver
    result = service.generate_equipment_set(
        role=role,
        profession=profession,
        specialization=specialization,
        mode=mode,
        experience=experience,
    )

    armor_assignment = result.equipment_set.armor
    gear_stats = result.base_stats

    full_stats = _merge_base_and_gear(BASE_STATS, gear_stats)
    derived = AttributeCalculator.calculate_all_derived_stats(full_stats)

    print("\n--- Armor assignment (slot -> prefix) ---")
    for slot, prefix in armor_assignment.items():
        print(f"  {slot:10s}: {prefix}")

    print("\n--- Aggregated gear stats (gear only) ---")
    for k in sorted(gear_stats.keys()):
        print(f"  {k:18s}: {gear_stats[k]}")

    print("\n--- Full stats with BASE_STATS ---")
    for k in sorted(full_stats.keys()):
        print(f"  {k:18s}: {full_stats[k]}")

    print("\n--- Derived stats ---")
    print(f"  Max Health: {int(derived['max_health'])}")
    print(f"  Toughness: {int(derived['toughness'])}")
    print(f"  Effective Power: {int(derived['effective_power'])}")
    print(f"  Crit Chance: {derived['crit_chance'] * 100:.1f}%")
    print(f"  Crit Damage Multiplier: {derived['crit_damage_multiplier']:.2f}x")

    print("\n--- Constraints ---")
    for key, val in sorted(result.constraints.min_stats.items()):
        print(f"  min {key:14s}: {val}")

    print("\nGreedy solver score:", result.score)
    print("Test finished. Inspect the distribution of prefixes per armor slot and HP vs. constraints.")


if __name__ == "__main__":
    main()
