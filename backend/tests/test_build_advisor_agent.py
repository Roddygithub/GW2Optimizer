import pytest

from app.agents.build_advisor_agent import BuildAdvisorAgent, BuildCandidate


def make_candidate(
    id: str,
    prefix: str,
    role: str,
    total_damage: float,
    survivability: float,
    overall_score: float | None = None,
):
    return BuildCandidate(
        id=id,
        prefix=prefix,
        role=role,
        rune="Scholar",
        sigils=["Force", "Impact"],
        total_damage=total_damage,
        survivability=survivability,
        overall_score=overall_score if overall_score is not None else total_damage,
    )


@pytest.mark.asyncio
async def test_dps_experience_influences_choice():
    advisor = BuildAdvisorAgent()

    # Deux presets: un très offensif mais fragile, un plus tanky mais un peu moins de DPS
    glass = make_candidate("glass", "Berserker", "dps", total_damage=100_000, survivability=1.0)
    tanky = make_candidate("tanky", "Marauder", "dps", total_damage=90_000, survivability=3.0)
    candidates = [glass, tanky]

    beginner_choice = advisor.choose_best_candidate(
        candidates=candidates,
        role="dps",
        context={"experience": "beginner", "mode": "wvw_zerg"},
    )
    expert_choice = advisor.choose_best_candidate(
        candidates=candidates,
        role="dps",
        context={"experience": "expert", "mode": "wvw_zerg"},
    )

    # Débutant: privilégier la survie -> preset Marauder plus tanky
    assert beginner_choice.candidate.prefix == "Marauder"

    # Expert: privilégier le DPS -> preset Berserker plus offensif
    assert expert_choice.candidate.prefix == "Berserker"


@pytest.mark.asyncio
async def test_support_beginner_vs_expert_alternatives_ranking():
    advisor = BuildAdvisorAgent()

    # Rôle support: le moteur utilise overall_score comme primaire
    # On simule un preset plus safe mais un peu moins performant, et un plus "greedy".
    safe = make_candidate(
        "safe",
        "Minstrel",
        "support",
        total_damage=40_000,
        survivability=3.0,
        overall_score=80.0,
    )
    greedy = make_candidate(
        "greedy",
        "Harrier",
        "support",
        total_damage=50_000,
        survivability=1.0,
        overall_score=100.0,
    )
    candidates = [safe, greedy]

    beginner_choice = advisor.choose_best_candidate(
        candidates=candidates,
        role="support",
        context={"experience": "beginner"},
    )
    expert_choice = advisor.choose_best_candidate(
        candidates=candidates,
        role="support",
        context={"experience": "expert"},
    )

    # Pour un support débutant, la variante plus tanky doit être privilégiée
    assert beginner_choice.candidate.prefix == "Minstrel"

    # Pour un support expert, la variante plus performante doit être en tête du ranking
    assert expert_choice.candidate.prefix == "Harrier"
    assert expert_choice.ranked_candidates is not None
    assert expert_choice.ranked_candidates[0].prefix == "Harrier"
