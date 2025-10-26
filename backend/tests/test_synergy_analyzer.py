"""Test synergy analyzer."""

import pytest
from datetime import datetime
from uuid import uuid4
from app.models.build import Build, GameMode, Profession, Role
from app.models.team import TeamComposition, TeamSlot
from app.services.synergy_analyzer import SynergyAnalyzer


@pytest.fixture
def analyzer():
    """Create synergy analyzer instance."""
    return SynergyAnalyzer()


@pytest.fixture
def sample_build():
    """Create sample build."""
    return Build(
        id=str(uuid4()),
        name="Test Guardian Build",
        profession=Profession.GUARDIAN,
        game_mode=GameMode.ZERG,
        role=Role.SUPPORT,
        user_id=str(uuid4()),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_team():
    """Create sample team with multiple builds."""
    team = TeamComposition(
        id=str(uuid4()),
        name="Test Team",
        game_mode=GameMode.ZERG,
        team_size=10,
        user_id=str(uuid4()),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Add diverse builds
    base_user_id = str(uuid4())
    now = datetime.utcnow()
    builds = [
        Build(
            id=str(uuid4()),
            name="Guardian Support",
            profession=Profession.GUARDIAN,
            game_mode=GameMode.ZERG,
            role=Role.SUPPORT,
            user_id=base_user_id,
            created_at=now,
            updated_at=now,
        ),
        Build(
            id=str(uuid4()),
            name="Warrior Tank",
            profession=Profession.WARRIOR,
            game_mode=GameMode.ZERG,
            role=Role.TANK,
            user_id=base_user_id,
            created_at=now,
            updated_at=now,
        ),
        Build(
            id=str(uuid4()),
            name="Mesmer DPS",
            profession=Profession.MESMER,
            game_mode=GameMode.ZERG,
            role=Role.DPS,
            user_id=base_user_id,
            created_at=now,
            updated_at=now,
        ),
        Build(
            id=str(uuid4()),
            name="Revenant DPS",
            profession=Profession.REVENANT,
            game_mode=GameMode.ZERG,
            role=Role.DPS,
            user_id=base_user_id,
            created_at=now,
            updated_at=now,
        ),
        Build(
            id=str(uuid4()),
            name="Engineer DPS",
            profession=Profession.ENGINEER,
            game_mode=GameMode.ZERG,
            role=Role.DPS,
            user_id=base_user_id,
            created_at=now,
            updated_at=now,
        ),
    ]

    team.slots = [
        TeamSlot(
            id=str(uuid4()),
            slot_number=i + 1,
            build=build,
            priority=1,
        )
        for i, build in enumerate(builds)
    ]

    return team


def test_get_boon_coverage(analyzer, sample_build):
    """Test boon coverage extraction."""
    boons = analyzer._get_boon_coverage(sample_build)
    assert isinstance(boons, list)
    assert len(boons) > 0
    # Guardian should provide multiple boons
    assert any(boon in boons for boon in ["aegis", "protection", "quickness"])


def test_evaluate_role_effectiveness(analyzer, sample_build):
    """Test role effectiveness evaluation."""
    score = analyzer._evaluate_role_effectiveness(sample_build)
    assert 0 <= score <= 10
    # Guardian support should score well
    assert score >= 5.0


def test_calculate_synergy_potential(analyzer, sample_build):
    """Test synergy potential calculation."""
    potential = analyzer._calculate_synergy_potential(sample_build)
    assert 0 <= potential <= 10


def test_identify_strengths(analyzer, sample_build):
    """Test strength identification."""
    strengths = analyzer._identify_strengths(sample_build)
    assert isinstance(strengths, list)
    # Guardian should have strengths
    assert len(strengths) > 0


def test_identify_weaknesses(analyzer, sample_build):
    """Test weakness identification."""
    weaknesses = analyzer._identify_weaknesses(sample_build)
    assert isinstance(weaknesses, list)


def test_analyze_build(analyzer, sample_build):
    """Test complete build analysis."""
    analysis = analyzer.analyze_build(sample_build)

    assert "boons_provided" in analysis
    assert "role_effectiveness" in analysis
    assert "synergy_potential" in analysis
    assert "strengths" in analysis
    assert "weaknesses" in analysis

    assert isinstance(analysis["boons_provided"], list)
    assert isinstance(analysis["role_effectiveness"], float)
    assert isinstance(analysis["strengths"], list)


def test_analyze_team(analyzer, sample_team):
    """Test team analysis."""
    synergies = analyzer.analyze_team(sample_team)

    assert isinstance(synergies, list)
    # Should find some synergies with diverse team
    assert len(synergies) > 0

    for synergy in synergies:
        assert hasattr(synergy, "synergy_type")
        assert hasattr(synergy, "description")
        assert hasattr(synergy, "strength")
        assert 0 <= synergy.strength <= 10


def test_calculate_team_score(analyzer, sample_team):
    """Test team scoring."""
    scores = analyzer.calculate_team_score(sample_team)

    assert "boon_coverage" in scores
    assert "role_balance" in scores
    assert "profession_diversity" in scores
    assert "overall" in scores

    # All scores should be 0-10
    for key, score in scores.items():
        assert 0 <= score <= 10


def test_score_boon_coverage(analyzer, sample_team):
    """Test boon coverage scoring."""
    score = analyzer._score_boon_coverage(sample_team)
    assert 0 <= score <= 10
    # Diverse team should have decent boon coverage
    assert score >= 3.0


def test_score_role_balance(analyzer, sample_team):
    """Test role balance scoring."""
    score = analyzer._score_role_balance(sample_team)
    assert 0 <= score <= 10


def test_score_profession_diversity(analyzer, sample_team):
    """Test profession diversity scoring."""
    score = analyzer._score_profession_diversity(sample_team)
    assert 0 <= score <= 10
    # Sample team has 5 different professions
    assert score >= 5.0


@pytest.mark.legacy
def test_empty_team(analyzer):
    """Test analysis with empty team."""
    from tests.factories import create_test_team_composition

    empty_team = create_test_team_composition(
        name="Empty Team",
        game_mode=GameMode.ZERG,
        team_size=0,
        slots=[],
    )

    synergies = analyzer.analyze_team(empty_team)
    assert synergies == []

    scores = analyzer.calculate_team_score(empty_team)
    assert scores["overall"] >= 0
