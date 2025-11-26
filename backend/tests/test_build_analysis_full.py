import pytest
from app.services.build_analysis_service import BuildAnalysisService


pytestmark = pytest.mark.asyncio


class DummyGW2Client:
    """Client GW2 factice pour tester analyze_build_full sans appels réseau."""

    async def get_specialization_details(self, spec_id: int):  # type: ignore[override]
        # Simule une spécialisation orientée support/boon (par ex. Firebrand)
        return {
            "id": spec_id,
            "name": "Firebrand",
            "description": "Support boon provider with quickness and stability.",
            "profession": "Guardian",
        }

    async def get_trait_details(self, trait_id: int):  # type: ignore[override]
        return {
            "id": trait_id,
            "name": "Lorem Ipsum",
            "description": "Grant allies might and quickness while healing them.",
        }

    async def get_skills(self, skill_ids):  # type: ignore[override]
        return [
            {
                "id": sid,
                "name": f"Skill {sid}",
                "description": "Heal allies and provide stability.",
                "type": "Utility",
                "slot": "Utility",
            }
            for sid in skill_ids
        ]


class DummyAnalystAgent:
    async def execute(self, payload):  # type: ignore[override]
        # Retourne un résultat minimal avec un résumé générique
        return {
            "success": True,
            "result": {
                "summary": "Dummy synergy analysis.",
            },
        }


class DummyOptimizer:
    async def optimize_build(self, base_stats, skill_rotation, role):  # type: ignore[override]
        # Retourne une structure minimale de type OptimizationResult-like
        class Result:
            def __init__(self, role: str):
                self.rune_name = "Rune of Leadership" if role != "dps" else "Rune of Scholar"
                self.sigil_names = ["Sigil of Concentration", "Sigil of Transference"]
                self.total_damage = 42_000.0
                self.survivability_score = 3.0
                self.overall_score = 123.4

        return Result(role)


async def test_analyze_build_full_uses_detected_role_before_context():
    gw2_client = DummyGW2Client()
    analyst = DummyAnalystAgent()
    optimizer = DummyOptimizer()

    service = BuildAnalysisService(gw2_client=gw2_client, analyst_agent=analyst, optimizer=optimizer)

    result = await service.analyze_build_full(
        specialization_id=999,
        trait_ids=[1, 2, 3],
        skill_ids=[101, 102],
        context="WvW Zerg DPS",  # le texte mentionne DPS mais les données incluent des signaux de support/boon
    )

    assert isinstance(result, dict)
    assert "gear_optimization" in result

    go = result["gear_optimization"]
    # Le rôle doit être support/boon (issu des données), pas purement "dps" du contexte texte
    assert go["role"] in {"support", "boon", "tank"}

    # Vérifier la forme de gear_optimization
    chosen = go["chosen"]
    assert "prefix" in chosen
    assert "rune" in chosen
    assert "sigils" in chosen
    assert isinstance(chosen["sigils"], list)
    assert "total_damage" in chosen
    assert "survivability" in chosen
    assert "overall_score" in chosen


async def test_analyze_build_full_derives_mode_and_experience_from_context():
    gw2_client = DummyGW2Client()
    analyst = DummyAnalystAgent()
    optimizer = DummyOptimizer()

    service = BuildAnalysisService(gw2_client=gw2_client, analyst_agent=analyst, optimizer=optimizer)

    result = await service.analyze_build_full(
        specialization_id=999,
        trait_ids=[1],
        skill_ids=[101],
        context="Smallscale roam, beginner guardian support.",
    )

    go = result["gear_optimization"]
    assert go["mode"] == "wvw_roam"
    assert go["experience"] == "beginner"
