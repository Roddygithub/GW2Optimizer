import pytest

from app.agents.team_commander_agent import TeamCommanderAgent, Role
from app.services.meta_build_catalog import MetaBuild, META_BUILD_REGISTRY
from app.services.meta_rag_service import MetaRAGService


def setup_function(_function):
    """Seed META_BUILD_REGISTRY with a simple heal meta build for outnumber."""

    META_BUILD_REGISTRY.clear()

    META_BUILD_REGISTRY["scrapper-heal-outnumber"] = MetaBuild(
        id="scrapper-heal-outnumber",
        name="Scrapper Heal Outnumber",
        profession="Engineer",
        specialization="Scrapper",
        role="heal",
        game_mode="wvw_outnumber",
        source="Hardstuck",
        tags=["wvw", "outnumber", "heal"],
        notes="Healing Scrapper build for smallscale/outnumber fights.",
        chat_code="[&ScrapHealOutnumber=]",
        stats_text="Minstrel / Harrier mix.",
        runes_text="Rune of the Monk",
    )


def test_select_class_for_role_prefers_meta_rag_suggestions_for_heal():
    """TeamCommander doit pouvoir préférer une classe issue des builds méta pour un rôle donné."""

    agent = TeamCommanderAgent(meta_rag=MetaRAGService())

    # Par défaut, ROLE_TO_CLASSES[HEAL] commence par "Ranger Druid".
    # Avec un build méta Engineer Scrapper (heal, wvw_outnumber), le RAG
    # doit pouvoir faire passer "Engineer Scrapper" en tête pour ce mode.
    class_spec = agent._select_class_for_role(Role.HEAL, mode="wvw_outnumber")

    assert class_spec == "Engineer Scrapper"
