"""Test GW2Skill parser."""

import pytest
from app.services.parser import gw2skill_parser as gw2skill_module
from app.services.parser.gw2skill_parser import GW2SkillParser


@pytest.mark.asyncio
async def test_normalize_url():
    """Test URL normalization."""
    parser = GW2SkillParser()

    # Test various URL formats
    urls = [
        ("gw2skills.net/editor/?test", "https://gw2skills.net/editor/?test"),
        ("en.gw2skills.net/editor/?test", "https://gw2skills.net/editor/?test"),
        ("fr.gw2skills.net/editor/?test", "https://gw2skills.net/editor/?test"),
        ("www.gw2skills.net/editor/?test", "https://gw2skills.net/editor/?test"),
        ("http://gw2skills.net/editor/?test", "https://gw2skills.net/editor/?test"),
    ]

    for input_url, expected in urls:
        result = parser._normalize_url(input_url)
        assert result == expected


@pytest.mark.asyncio
async def test_extract_profession():
    """Test profession extraction from URL."""
    parser = GW2SkillParser()

    test_cases = [
        ("https://gw2skills.net/editor/?guardian", "Guardian"),
        ("https://gw2skills.net/editor/?warrior", "Warrior"),
        ("https://gw2skills.net/editor/?mesmer", "Mesmer"),
    ]

    for url, expected_prof in test_cases:
        profession = parser._extract_profession(url)
        assert profession is not None
        assert profession.value == expected_prof


@pytest.mark.asyncio
async def test_extract_build_name():
    """Test build name extraction."""
    from bs4 import BeautifulSoup

    parser = GW2SkillParser()

    # Test with title tag
    html = "<html><head><title>Test Build - GW2Skills.net</title></head></html>"
    soup = BeautifulSoup(html, "html.parser")
    name = parser._extract_build_name(soup)
    assert "Test Build" in name

    # Test with meta tag
    html = '<html><head><meta property="og:title" content="My Build"/></head></html>'
    soup = BeautifulSoup(html, "html.parser")
    name = parser._extract_build_name(soup)
    assert name == "My Build"


@pytest.mark.asyncio
async def test_parse_trait_lines():
    """Test trait line parsing."""
    from bs4 import BeautifulSoup

    parser = GW2SkillParser()

    # Test with script containing trait data
    html = """
    <html>
    <script>
    var traits = [123, 456, 789];
    </script>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    trait_lines = parser._parse_trait_lines(soup, {})

    assert len(trait_lines) > 0


@pytest.mark.asyncio
async def test_parse_skills():
    """Test skill parsing."""
    from bs4 import BeautifulSoup

    parser = GW2SkillParser()

    # Test with script containing skill data
    html = """
    <html>
    <script>
    var skills = [1001, 2002, 3003, 4004, 5005];
    </script>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    skills = parser._parse_skills(soup, {})

    assert len(skills) > 0
    assert all(skill.slot in ["Heal", "Utility1", "Utility2", "Utility3", "Elite"] for skill in skills[:5])


@pytest.mark.asyncio
async def test_parse_equipment():
    """Test equipment parsing."""
    from bs4 import BeautifulSoup

    parser = GW2SkillParser()

    # Test with script containing equipment data
    html = """
    <html>
    <script>
    var equipment = {stats: "Berserker"};
    </script>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    equipment = parser._parse_equipment(soup, {})

    assert len(equipment) > 0
    assert all(hasattr(eq, "slot") for eq in equipment)


@pytest.mark.asyncio
async def test_ai_profession_inference_french_synonym(monkeypatch):
    """AI fallback should map French profession names to internal enums.

    This exercises _infer_profession_from_page by mocking both the HTTP
    client (httpx.AsyncClient) and the Ollama service so that the test is
    fully deterministic and offline.
    """

    # Mock HTTP client used inside _infer_profession_from_page
    class DummyResponse:
        def __init__(self) -> None:
            self.text = "<html><body>Build Gardien WvW</body></html>"

        def raise_for_status(self) -> None:  # pragma: no cover - trivial
            return None

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):  # type: ignore[override]
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
            return None

        async def get(self, url: str) -> DummyResponse:  # type: ignore[override]
            return DummyResponse()

    monkeypatch.setattr(gw2skill_module.httpx, "AsyncClient", DummyClient)

    # Mock AI service to return a French profession name
    class DummyAI:
        async def generate_structured(self, **kwargs):  # type: ignore[override]
            return {"profession": "Gardien"}

    parser = GW2SkillParser(ai_service=DummyAI())

    profession = await parser._infer_profession_from_page("https://gw2skills.net/editor/?dummy")

    assert profession is not None
    assert profession.value == "Guardian"
