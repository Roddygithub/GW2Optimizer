import pytest

from app.agents.build_equipment_optimizer import BuildEquipmentOptimizer
from app.engine.gear.registry import RUNE_REGISTRY, SIGIL_REGISTRY
from app.engine.modifiers.base import ModifierType


pytestmark = pytest.mark.asyncio


def _classify_rune(name: str) -> dict:
    """Retourne un dict de flags (has_heal/boon/tank/dps) pour une rune donnée."""
    mods = RUNE_REGISTRY[name]()
    has_heal = any(
        (m.target_stat == "healing_power" and m.modifier_type in {ModifierType.FLAT_STAT, ModifierType.PERCENT_STAT})
        or m.modifier_type in {ModifierType.OUTGOING_HEALING, ModifierType.INCOMING_HEALING}
        for m in mods
    )
    has_boon = any(
        m.modifier_type == ModifierType.BOON_DURATION or m.target_stat == "concentration" for m in mods
    )
    has_tank = any(m.target_stat in {"toughness", "vitality"} for m in mods)
    has_dps = any(
        m.target_stat in {"power", "precision", "ferocity", "condition_damage"}
        or m.modifier_type
        in {
            ModifierType.DAMAGE_MULTIPLIER,
            ModifierType.STRIKE_DAMAGE_MULTIPLIER,
            ModifierType.CONDITION_DAMAGE_MULTIPLIER,
            ModifierType.PROC_DAMAGE,
        }
        for m in mods
    )
    return {
        "has_heal": has_heal,
        "has_boon": has_boon,
        "has_tank": has_tank,
        "has_dps": has_dps,
    }


def _classify_sigil(name: str) -> dict:
    """Retourne un dict de flags (has_heal/boon/tank/dps) pour un sigil donné."""
    factory = SIGIL_REGISTRY[name]
    try:
        mod = factory()
    except TypeError:
        mod = factory(25)  # type: ignore[misc]

    has_heal = mod.target_stat == "healing_power" or mod.modifier_type in {
        ModifierType.OUTGOING_HEALING,
        ModifierType.INCOMING_HEALING,
    }
    has_boon = mod.modifier_type == ModifierType.BOON_DURATION or mod.target_stat == "concentration"
    has_tank = mod.target_stat in {"toughness", "vitality"}
    has_dps = (
        mod.target_stat in {"power", "precision", "ferocity", "condition_damage"}
        or mod.modifier_type
        in {
            ModifierType.DAMAGE_MULTIPLIER,
            ModifierType.STRIKE_DAMAGE_MULTIPLIER,
            ModifierType.CONDITION_DAMAGE_MULTIPLIER,
            ModifierType.PROC_DAMAGE,
        }
    )
    return {
        "has_heal": has_heal,
        "has_boon": has_boon,
        "has_tank": has_tank,
        "has_dps": has_dps,
    }


class TestBuildEquipmentOptimizerRoles:
    async def test_heal_role_prefers_support_runes_and_sigils(self) -> None:
        optimizer = BuildEquipmentOptimizer()

        base_stats = {
            "power": 1200,
            "precision": 1000,
            "ferocity": 0,
            "toughness": 1400,
            "vitality": 1400,
            "condition_damage": 0,
            "expertise": 0,
            "concentration": 1200,
            "healing_power": 1800,
        }
        rotation = [
            {"name": "Heal Test Skill", "damage_coefficient": 0.5},
        ]

        result = await optimizer.optimize_build(
            base_stats=base_stats,
            skill_rotation=rotation,
            role="heal",
        )

        rune_flags = _classify_rune(result.rune_name)
        # Une rune de heal doit au moins apporter du heal ou des boons
        assert rune_flags["has_heal"] or rune_flags["has_boon"]
        # Ne doit pas être une rune purement DPS
        assert not (rune_flags["has_dps"] and not (rune_flags["has_heal"] or rune_flags["has_boon"]))

        for sigil in result.sigil_names:
            sig_flags = _classify_sigil(sigil)
            # Les sigils offensifs purs (Force, Impact, ...) ne devraient plus apparaître pour HEAL
            assert not (sig_flags["has_dps"] and not (sig_flags["has_heal"] or sig_flags["has_boon"] or sig_flags["has_tank"]))

    async def test_dps_role_uses_offensive_runes_and_sigils(self) -> None:
        optimizer = BuildEquipmentOptimizer()

        base_stats = {
            "power": 2800,
            "precision": 2200,
            "ferocity": 1200,
            "toughness": 1000,
            "vitality": 1000,
            "condition_damage": 0,
            "expertise": 0,
            "concentration": 0,
            "healing_power": 0,
        }
        rotation = [
            {"name": "Burst Skill", "damage_coefficient": 2.0},
        ]

        result = await optimizer.optimize_build(
            base_stats=base_stats,
            skill_rotation=rotation,
            role="dps",
        )

        rune_flags = _classify_rune(result.rune_name)
        assert rune_flags["has_dps"]

        # Au moins un sigil doit être orienté dégâts
        sig_flags_list = [_classify_sigil(s) for s in result.sigil_names]
        assert any(f["has_dps"] for f in sig_flags_list)

    async def test_tank_role_prefers_defensive_runes_and_sigils(self) -> None:
        optimizer = BuildEquipmentOptimizer()

        base_stats = {
            "power": 1600,
            "precision": 1200,
            "ferocity": 400,
            "toughness": 1800,
            "vitality": 1800,
            "condition_damage": 0,
            "expertise": 0,
            "concentration": 1400,
            "healing_power": 600,
        }
        rotation = [
            {"name": "Tank Skill", "damage_coefficient": 1.0},
        ]

        result = await optimizer.optimize_build(
            base_stats=base_stats,
            skill_rotation=rotation,
            role="tank",
        )

        rune_flags = _classify_rune(result.rune_name)
        # Tank: priorité aux runes avec toughness/vitality ou boon duration
        assert rune_flags["has_tank"] or rune_flags["has_boon"]

        for sigil in result.sigil_names:
            sig_flags = _classify_sigil(sigil)
            # Sigils défensifs (toughness/heal/boon) autorisés, éviter les combos full DPS
            assert not (sig_flags["has_dps"] and not (sig_flags["has_heal"] or sig_flags["has_tank"]))


class TestBuildEquipmentOptimizerTopK:
    async def test_topk_contains_best_candidate(self) -> None:
        optimizer = BuildEquipmentOptimizer()

        base_stats = {
            "power": 2800,
            "precision": 2200,
            "ferocity": 1200,
            "toughness": 1000,
            "vitality": 1000,
            "condition_damage": 0,
            "expertise": 0,
            "concentration": 0,
            "healing_power": 0,
        }
        rotation = [
            {"name": "Burst Skill", "damage_coefficient": 2.0},
        ]

        best = await optimizer.optimize_build(
            base_stats=base_stats,
            skill_rotation=rotation,
            role="dps",
        )

        top_candidates = await optimizer.optimize_build_top_k(
            base_stats=base_stats,
            skill_rotation=rotation,
            role="dps",
            top_k=5,
        )

        assert len(top_candidates) >= 1
        max_score = max(c.overall_score for c in top_candidates)
        assert max_score == pytest.approx(best.overall_score)

    async def test_topk_is_sorted_by_score_desc(self) -> None:
        optimizer = BuildEquipmentOptimizer()

        base_stats = {
            "power": 2800,
            "precision": 2200,
            "ferocity": 1200,
            "toughness": 1000,
            "vitality": 1000,
            "condition_damage": 0,
            "expertise": 0,
            "concentration": 0,
            "healing_power": 0,
        }
        rotation = [
            {"name": "Burst Skill", "damage_coefficient": 2.0},
        ]

        top_candidates = await optimizer.optimize_build_top_k(
            base_stats=base_stats,
            skill_rotation=rotation,
            role="dps",
            top_k=5,
        )

        scores = [c.overall_score for c in top_candidates]
        assert scores == sorted(scores, reverse=True)
