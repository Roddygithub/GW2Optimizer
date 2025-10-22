"""Test Snowcrows exporter."""

import pytest
import json
from app.models.build import Build, GameMode, Profession, Role, TraitLine, Skill, Equipment
from app.models.team import TeamComposition, TeamSlot
from app.services.exporter.snowcrows_exporter import SnowcrowsExporter
from tests.factories import create_test_build, create_test_team_composition, create_test_team_slot


@pytest.fixture
def exporter():
    """Create exporter instance."""
    return SnowcrowsExporter()


@pytest.fixture
def sample_build():
    """Create sample build with all data."""
    return create_test_build(
        name="Test Guardian Build",
        profession=Profession.GUARDIAN,
        specialization="Firebrand",
        game_mode=GameMode.ZERG,
        role=Role.SUPPORT,
        trait_lines=[
            TraitLine(id=1, name="Radiance", traits=[123, 456, 789]),
            TraitLine(id=2, name="Valor", traits=[111, 222, 333]),
        ],
        skills=[
            Skill(slot="Heal", id=1001, name="Shelter"),
            Skill(slot="Utility1", id=2001, name="Mantra of Solace"),
        ],
        equipment=[
            Equipment(slot="Helm", id=3001, name="Minstrel Helm", stats="Minstrel"),
            Equipment(slot="Coat", id=3002, name="Minstrel Coat", stats="Minstrel"),
        ],
        description="Test build description",
        playstyle="Defensive support playstyle",
        synergies=["Works well with DPS", "Provides stability"],
        counters=["Weak against condition pressure"],
        effectiveness=8.5,
        difficulty=3,
    )


@pytest.fixture
def sample_team(sample_build):
    """Create sample team."""
    team = create_test_team_composition(
        name="Test Team",
        game_mode=GameMode.ZERG,
        team_size=5,
        overall_rating=8.0,
        strengths=["Good boon coverage"],
        weaknesses=["Low mobility"],
    )

    team.slots = [
        create_test_team_slot(slot_number=1, build=sample_build, player_name="Player1", priority=1),
        create_test_team_slot(slot_number=2, build=sample_build, player_name="Player2", priority=2),
    ]

    return team


@pytest.mark.legacy
def test_export_build_json(exporter, sample_build):
    """Test build JSON export."""
    result = exporter.export_build_json(sample_build)

    assert isinstance(result, dict)
    assert result["name"] == "Test Guardian Build"
    assert result["profession"] == "Guardian"
    assert result["specialization"] == "Firebrand"
    assert "traits" in result
    assert "skills" in result
    assert "equipment" in result
    assert "metadata" in result

    # Check metadata
    metadata = result["metadata"]
    assert metadata["game_mode"] == "zerg"
    assert metadata["role"] == "support"
    assert metadata["effectiveness"] == 8.5
    assert metadata["difficulty"] == 3


@pytest.mark.legacy
def test_export_traits(exporter, sample_build):
    """Test trait export."""
    traits = exporter._export_traits(sample_build.trait_lines)

    assert isinstance(traits, list)
    assert len(traits) == 2
    assert traits[0]["name"] == "Radiance"
    assert traits[0]["traits"] == [123, 456, 789]


@pytest.mark.legacy
def test_export_skills(exporter, sample_build):
    """Test skill export."""
    skills = exporter._export_skills(sample_build.skills)

    assert isinstance(skills, list)
    assert len(skills) == 2
    assert skills[0]["slot"] == "Heal"
    assert skills[0]["name"] == "Shelter"


@pytest.mark.legacy
def test_export_equipment(exporter, sample_build):
    """Test equipment export."""
    equipment = exporter._export_equipment(sample_build.equipment)

    assert isinstance(equipment, list)
    assert len(equipment) == 2
    assert equipment[0]["slot"] == "Helm"
    assert equipment[0]["stats"] == "Minstrel"


@pytest.mark.legacy
def test_export_build_html(exporter, sample_build):
    """Test build HTML export."""
    html = exporter.export_build_html(sample_build)

    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "Test Guardian Build" in html
    assert "Guardian" in html
    assert "Firebrand" in html
    assert "support" in html

    # Check CSS is included
    assert "<style>" in html
    assert "build-container" in html


@pytest.mark.legacy
def test_export_team_json(exporter, sample_team):
    """Test team JSON export."""
    result = exporter.export_team_json(sample_team)

    assert isinstance(result, dict)
    assert result["name"] == "Test Team"
    assert result["game_mode"] == "zerg"
    assert result["team_size"] == 5
    assert "slots" in result
    assert len(result["slots"]) == 2

    # Check slot structure
    slot = result["slots"][0]
    assert slot["slot_number"] == 0
    assert slot["player_name"] == "Player1"
    assert "build" in slot

    # Check metadata
    assert "metadata" in result
    assert "exported_at" in result["metadata"]


def test_get_snowcrows_css(exporter):
    """Test CSS generation."""
    css = exporter._get_snowcrows_css()

    assert isinstance(css, str)
    assert len(css) > 0
    assert "build-container" in css
    assert "build-header" in css
    assert "#c89b3c" in css  # GW2 gold color


@pytest.mark.legacy
def test_render_trait_lines_html(exporter, sample_build):
    """Test trait lines HTML rendering."""
    html = exporter._render_trait_lines_html(sample_build.trait_lines)

    assert isinstance(html, str)
    assert "Radiance" in html
    assert "Valor" in html
    assert "trait-line" in html


@pytest.mark.legacy
def test_render_skills_html(exporter, sample_build):
    """Test skills HTML rendering."""
    html = exporter._render_skills_html(sample_build.skills)

    assert isinstance(html, str)
    assert "Heal" in html
    assert "Shelter" in html
    assert "skill" in html


@pytest.mark.legacy
def test_render_equipment_html(exporter, sample_build):
    """Test equipment HTML rendering."""
    html = exporter._render_equipment_html(sample_build.equipment)

    assert isinstance(html, str)
    assert "Helm" in html
    assert "Minstrel" in html
    assert "equipment-item" in html


def test_export_empty_build(exporter):
    """Test exporting build with minimal data."""
    minimal_build = Build(
        name="Minimal Build",
        profession=Profession.WARRIOR,
        game_mode=GameMode.ROAMING,
        role=Role.DPS,
    )

    result = exporter.export_build_json(minimal_build)
    assert result["name"] == "Minimal Build"
    assert result["profession"] == "Warrior"
    assert len(result["traits"]) == 0
    assert len(result["skills"]) == 0
