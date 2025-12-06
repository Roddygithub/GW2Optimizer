import pytest

from app.engine.combat.context import CombatContext
from app.engine.simulation.rotation import RotationSimulator, RotationSkill


def test_rotation_simulator_single_skill_basic():
    """Un skill simple doit générer des dégâts positifs et plusieurs lancers sur 10s."""
    sim = RotationSimulator()
    ctx = CombatContext.create_default()

    skills = [
        RotationSkill(
            name="Test Skill",
            damage_coefficient=1.0,
            cast_time=1.0,
            cooldown=1.0,
        )
    ]

    result = sim.simulate_rotation(
        base_stats={"power": 1500, "precision": 1500, "ferocity": 1500, "condition_damage": 0},
        modifiers=[],
        context=ctx,
        skills=skills,
        duration=10.0,
        weapon_strength=1000,
    )

    assert result["total_damage"] > 0
    assert result["dps"] > 0
    per_skill = result["per_skill"].get("Test Skill")
    assert per_skill is not None
    # On doit avoir plusieurs lancers sur 10s
    assert per_skill["casts"] >= 5


def test_rotation_simulator_respects_priority_and_cooldown():
    """Le simulateur doit respecter les priorités et temps de recharge basiques."""
    sim = RotationSimulator()
    ctx = CombatContext.create_default()

    high_priority = RotationSkill(
        name="High Priority",
        damage_coefficient=2.0,
        cast_time=1.0,
        cooldown=5.0,
        priority=0,
    )
    low_priority = RotationSkill(
        name="Low Priority",
        damage_coefficient=1.0,
        cast_time=1.0,
        cooldown=1.0,
        priority=1,
    )

    result = sim.simulate_rotation(
        base_stats={"power": 1500, "precision": 1500, "ferocity": 1500, "condition_damage": 0},
        modifiers=[],
        context=ctx,
        skills=[high_priority, low_priority],
        duration=10.0,
        weapon_strength=1000,
    )

    per_skill = result["per_skill"]
    # Le skill haute priorité doit être lancé au moins une fois
    assert per_skill.get("High Priority", {}).get("casts", 0) >= 1
    # Le skill basse priorité doit être lancé plusieurs fois
    assert per_skill.get("Low Priority", {}).get("casts", 0) >= 3


def test_rotation_simulator_healing_produces_hps():
    """Un skill avec heal_coefficient doit produire un total_heal et un HPS positifs."""
    sim = RotationSimulator()
    ctx = CombatContext.create_default()

    heal_skill = RotationSkill(
        name="Test Heal",
        damage_coefficient=0.0,
        cast_time=1.0,
        cooldown=1.0,
        heal_coefficient=0.5,
        base_heal=1000.0,
    )

    result = sim.simulate_rotation(
        base_stats={
            "power": 0,
            "precision": 0,
            "ferocity": 0,
            "condition_damage": 0,
            "healing_power": 1500,
        },
        modifiers=[],
        context=ctx,
        skills=[heal_skill],
        duration=10.0,
        weapon_strength=1000,
    )

    assert result["total_heal"] > 0.0
    assert result["hps"] > 0.0
    per_skill = result["per_skill"].get("Test Heal")
    assert per_skill is not None
    assert per_skill["total_heal"] > 0.0
