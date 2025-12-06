import pytest
from app.services.build_analysis_service import BuildAnalysisService


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
        # Retourne un résultat minimal avec un résumé générique, en propageant
        # build_data pour que BuildAnalysisService puisse choisir une rotation
        # spécifique (par ex. Firebrand support).
        build_data = payload.get("build_data")
        return {
            "success": True,
            "result": {
                "summary": "Dummy synergy analysis.",
                "build_data": build_data,
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
                # Champ optionnel attendu par BuildAnalysisService lorsqu'il construit les candidats
                self.relic_name = None
                # Simuler un breakdown contenant les métriques de rotation pour tester leur exposition
                self.breakdown = {
                    "rotation_dps_10s": 1234.5,
                    "rotation_total_damage_10s": 12_345.0,
                    "rotation_hps_10s": 2222.2,
                    "rotation_total_heal_10s": 20_000.0,
                }

        return Result(role)


class DummyGw2DataService:
    """Service GW2 factice pour stabiliser les tests sans dépendre des dumps JSON réels."""

    def detect_role(self, spec_id=None, trait_ids=None, skill_ids=None, context: str = ""):
        class RoleAnalysisLike:
            def __init__(self) -> None:
                self.primary_role = "support"
                self.confidence = 0.9
                self.secondary_roles = []

        return RoleAnalysisLike()

    def get_meta_context_string(
        self,
        game_mode: str = "wvw",
        profession=None,
        specialization=None,
        role=None,
        user_build_data=None,
    ) -> str:
        return ""

    def compare_build_to_meta(
        self,
        spec_id=None,
        trait_ids=None,
        skill_ids=None,
        gear_optimization=None,
        context: str = "",
    ):
        return {
            "closest_meta": None,
            "similarity_score": 0.0,
            "recommendations": [],
            "equipment_comparison": None,
            "user_role": "support",
            "role_confidence": 0.9,
        }


async def test_analyze_build_full_uses_detected_role_before_context():
    gw2_client = DummyGW2Client()
    analyst = DummyAnalystAgent()
    optimizer = DummyOptimizer()
    gw2_data = DummyGw2DataService()

    service = BuildAnalysisService(
        gw2_client=gw2_client,
        analyst_agent=analyst,
        optimizer=optimizer,
        gw2_data_service=gw2_data,
    )

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
    # Les métriques de rotation doivent être exposées lorsque présentes dans breakdown
    assert chosen.get("rotation_dps_10s") == 1234.5
    assert chosen.get("rotation_total_damage_10s") == 12_345.0
    assert chosen.get("rotation_hps_10s") == 2222.2
    assert chosen.get("rotation_total_heal_10s") == 20_000.0


async def test_analyze_build_full_derives_mode_and_experience_from_context():
    gw2_client = DummyGW2Client()
    analyst = DummyAnalystAgent()
    optimizer = DummyOptimizer()
    gw2_data = DummyGw2DataService()

    service = BuildAnalysisService(
        gw2_client=gw2_client,
        analyst_agent=analyst,
        optimizer=optimizer,
        gw2_data_service=gw2_data,
    )

    result = await service.analyze_build_full(
        specialization_id=999,
        trait_ids=[1],
        skill_ids=[101],
        context="Smallscale roam, beginner guardian support.",
    )

    go = result["gear_optimization"]
    assert go["mode"] == "wvw_roam"
    assert go["experience"] == "beginner"


def test_select_skill_rotation_for_firebrand_support_uses_firebrand_rotation():
    """_select_skill_rotation_for_build doit choisir la rotation Firebrand pour un build FB support."""

    from app.engine.simulation.rotation import get_firebrand_support_wvw_rotation

    gw2_client = DummyGW2Client()
    analyst = DummyAnalystAgent()
    optimizer = DummyOptimizer()
    gw2_data = DummyGw2DataService()

    service = BuildAnalysisService(
        gw2_client=gw2_client,
        analyst_agent=analyst,
        optimizer=optimizer,
        gw2_data_service=gw2_data,
    )

    synergy_result = {
        "build_data": {
            "context": "WvW Zerg",
            "specialization": {
                "id": 999,
                "name": "Firebrand",
                "description": "Support boon provider with quickness and stability.",
                "profession": "Guardian",
            },
            "traits": [],
            "skills": [],
            "detected_role": "support",
        },
        "detected_role": "support",
    }

    rotation = service._select_skill_rotation_for_build(synergy_result, "support")
    fb_rotation = get_firebrand_support_wvw_rotation()

    assert [s["name"] for s in rotation] == [s["name"] for s in fb_rotation]


def test_select_skill_rotation_for_reaper_dps_uses_reaper_rotation():
    """_select_skill_rotation_for_build doit choisir la rotation Reaper pour un build Reaper DPS."""

    from app.engine.simulation.rotation import get_reaper_power_wvw_rotation

    gw2_client = DummyGW2Client()
    analyst = DummyAnalystAgent()
    optimizer = DummyOptimizer()
    gw2_data = DummyGw2DataService()

    service = BuildAnalysisService(
        gw2_client=gw2_client,
        analyst_agent=analyst,
        optimizer=optimizer,
        gw2_data_service=gw2_data,
    )

    synergy_result = {
        "build_data": {
            "context": "WvW Zerg",
            "specialization": {
                "id": 55,
                "name": "Reaper",
                "description": "Power DPS reaper build.",
                "profession": "Necromancer",
            },
            "traits": [],
            "skills": [],
            "detected_role": "dps",
        },
        "detected_role": "dps",
    }

    rotation = service._select_skill_rotation_for_build(synergy_result, "dps")
    reaper_rotation = get_reaper_power_wvw_rotation()

    assert [s["name"] for s in rotation] == [s["name"] for s in reaper_rotation]
