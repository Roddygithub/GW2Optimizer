import pytest
from datetime import datetime

from app.services.parser.gw2skill_parser import GW2SkillParser
from app.models.build import Build, Profession, GameMode, Role, TraitLine, Skill, Equipment


pytestmark = pytest.mark.asyncio


async def test_gw2skill_parser_compact_url_uses_ai_fallback(monkeypatch):
    parser = GW2SkillParser()

    async def fake_fetch_build_page(url: str):  # type: ignore[override]
        return {
            "name": "Test Compact Build",
            "trait_lines": [],
            "skills": [],
            "equipment": [],
            "description": "Dummy description",
        }

    async def fake_infer_profession(url: str):  # type: ignore[override]
        return Profession.GUARDIAN

    monkeypatch.setattr(parser, "_fetch_build_page", fake_fetch_build_page)
    monkeypatch.setattr(parser, "_infer_profession_from_page", fake_infer_profession)

    # Compact GW2Skills URLs typically have only a ?PWwAk... query and no profession in the path
    url = "https://gw2skills.net/editor/?PWwAk-example-compact-code"

    build = await parser.parse_url(url)

    assert build is not None
    assert build.profession == Profession.GUARDIAN
    assert build.name == "Test Compact Build"


async def test_gw2skill_parser_uses_plan_b_when_ai_profession_fails(monkeypatch):
    parser = GW2SkillParser()

    async def fake_fetch_build_page(url: str):  # type: ignore[override]
        return {
            "name": "Should Not Be Used",
            "trait_lines": [],
            "skills": [],
            "equipment": [],
            "description": "Dummy description",
        }

    async def fake_infer_profession(url: str):  # type: ignore[override]
        return None

    now = datetime.utcnow()
    plan_b_build = Build(
        id="planb-1",
        user_id="test-user",
        created_at=now,
        updated_at=now,
        name="Plan B Build",
        profession=Profession.GUARDIAN,
        specialization="Firebrand",
        game_mode=GameMode.ZERG,
        role=Role.DPS,
        description="Plan B description",
        playstyle=None,
        source_url="https://gw2skills.net/editor/?dummy",
        source_type="gw2skill-planb",
        effectiveness=None,
        difficulty=None,
        is_public=False,
        trait_lines=[],
        skills=[],
        equipment=[],
        synergies=[],
        counters=[],
    )

    async def fake_plan_b(url: str):  # type: ignore[override]
        return plan_b_build

    monkeypatch.setattr(parser, "_fetch_build_page", fake_fetch_build_page)
    monkeypatch.setattr(parser, "_infer_profession_from_page", fake_infer_profession)
    monkeypatch.setattr(parser, "_plan_b_from_page", fake_plan_b)

    url = "https://gw2skills.net/editor/?PWwAk-plan-b-test"

    build = await parser.parse_url(url)

    assert build is plan_b_build
