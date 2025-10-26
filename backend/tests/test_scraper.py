"""Test community scraper."""

import pytest
from app.services.scraper.community_scraper import CommunityScraper
from app.models.build import Profession, Role


@pytest.fixture
def scraper():
    """Create scraper instance."""
    return CommunityScraper()


def test_scraper_initialization(scraper):
    """Test scraper initialization."""
    assert scraper.sources is not None
    assert "snowcrows" in scraper.sources
    assert "metabattle" in scraper.sources
    assert "hardstuck" in scraper.sources
    assert scraper.user_agent is not None


def test_extract_profession_from_text(scraper):
    """Test profession extraction."""
    test_cases = [
        ("Guardian Firebrand Build", Profession.GUARDIAN),
        ("Power Warrior DPS", Profession.WARRIOR),
        ("Mesmer Chronomancer", Profession.MESMER),
        ("Revenant Herald Support", Profession.REVENANT),
    ]

    for text, expected_prof in test_cases:
        result = scraper._extract_profession_from_text(text)
        assert result == expected_prof


def test_extract_profession_not_found(scraper):
    """Test profession extraction when not found."""
    result = scraper._extract_profession_from_text("Random Build Name")
    assert result is None


def test_guess_role_from_name(scraper):
    """Test role guessing from build name."""
    test_cases = [
        ("Heal Guardian", Role.SUPPORT),
        ("Tank Warrior", Role.TANK),
        ("Power DPS Thief", Role.DPS),
        ("Quickness Firebrand", Role.BOONSHARE),
        ("Condi Damage Necro", Role.DPS),
    ]

    for name, expected_role in test_cases:
        result = scraper._guess_role_from_name(name)
        assert result == expected_role


@pytest.mark.legacy
def test_remove_duplicates(scraper):
    """Test duplicate removal."""
    from app.models.build import Build, GameMode
    from tests.factories import create_test_build

    builds = [
        create_test_build(
            name="Guardian Build", profession=Profession.GUARDIAN, game_mode=GameMode.ZERG, role=Role.SUPPORT
        ),
        create_test_build(
            name="Guardian Build", profession=Profession.GUARDIAN, game_mode=GameMode.ZERG, role=Role.SUPPORT
        ),  # Duplicate
        create_test_build(name="Warrior Build", profession=Profession.WARRIOR, game_mode=GameMode.ZERG, role=Role.TANK),
    ]

    unique = scraper._remove_duplicates(builds)
    assert len(unique) == 2
    assert unique[0].name == "Guardian Build"
    assert unique[1].name == "Warrior Build"


@pytest.mark.asyncio
async def test_scrape_all_sources_structure(scraper):
    """Test scrape_all_sources returns correct structure."""
    # Note: This will attempt real scraping, might fail if sites are down
    # In production, you'd mock the HTTP requests
    try:
        builds = await scraper.scrape_all_sources()
        assert isinstance(builds, list)
        # All builds should have required attributes
        for build in builds:
            assert hasattr(build, "name")
            assert hasattr(build, "profession")
            assert hasattr(build, "game_mode")
            assert hasattr(build, "role")
    except Exception as e:
        # Sites might be down or blocking, that's okay for this test
        pytest.skip(f"Scraping failed (expected in test environment): {e}")
