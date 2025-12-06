import pytest

from app.services.meta_rag_service import MetaRAGService
from app.services.meta_build_catalog import MetaBuild, META_BUILD_REGISTRY


def setup_function(_function):
    """Reset META_BUILD_REGISTRY and seed it with a few sample builds."""

    META_BUILD_REGISTRY.clear()

    META_BUILD_REGISTRY["fb-support-wvw-zerg"] = MetaBuild(
        id="fb-support-wvw-zerg",
        name="Firebrand Support Zerg",
        profession="Guardian",
        specialization="Firebrand",
        role="support",
        game_mode="wvw_zerg",
        source="Hardstuck",
        tags=["wvw", "zerg", "support"],
        notes="Classic guardian firebrand support build for zergs.",
        chat_code="[&DQEQGi8fGybZEgAAXQEAAG8BAAC0EgAAwhIAAAAAAAAAAAAAAAAAAAAAAAA=]",
        stats_text="Full Minstrel stats with some Cleric pieces.",
        runes_text="Rune of Leadership",
    )

    META_BUILD_REGISTRY["reaper-dps-wvw-zerg"] = MetaBuild(
        id="reaper-dps-wvw-zerg",
        name="Reaper Power Zerg",
        profession="Necromancer",
        specialization="Reaper",
        role="dps",
        game_mode="wvw_zerg",
        source="Snowcrows",
        tags=["wvw", "zerg", "dps"],
        notes="High burst power DPS reaper for zerg fights.",
        chat_code="[&DQg1Gi0bOwqXEQAABhEAAFgBAADUEgAAwhIAAAAAAAAAAAAAAAAAAAAAAAA=]",
        stats_text="Berserker / Marauder mix.",
        runes_text="Rune of Scholar",
    )


def test_retrieve_for_build_filters_by_profession_and_role():
    service = MetaRAGService()

    hits = service.retrieve_for_build(
        game_mode="wvw_zerg",
        profession="Guardian",
        specialization="Firebrand",
        role="support",
        question="guardian firebrand support wvw zerg with stability and boons",
        max_results=5,
    )

    assert hits
    top = hits[0]
    assert top["profession"] == "Guardian"
    assert top["specialization"] == "Firebrand"
    assert top["role"] == "support"
    # Reaper build should either be absent or come after Firebrand in ranking
    names = [h["name"] for h in hits]
    assert names[0] == "Firebrand Support Zerg"


def test_build_context_for_build_produces_compact_text():
    service = MetaRAGService()

    ctx = service.build_context_for_build(
        game_mode="wvw_zerg",
        profession="Guardian",
        specialization="Firebrand",
        role="support",
        question="stab quickness boon support for wvw zerg",
        max_results=2,
        max_chars=500,
    )

    assert ctx is not None
    assert "Meta RAG context" in ctx
    # Doit mentionner au moins un build et sa source
    assert "Firebrand Support Zerg" in ctx
    assert "Hardstuck" in ctx
    # Respect du plafond de taille
    assert len(ctx) <= 500

