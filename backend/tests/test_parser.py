"""Test GW2Skill parser."""

import pytest
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
    soup = BeautifulSoup(html, 'html.parser')
    name = parser._extract_build_name(soup)
    assert "Test Build" in name
    
    # Test with meta tag
    html = '<html><head><meta property="og:title" content="My Build"/></head></html>'
    soup = BeautifulSoup(html, 'html.parser')
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
    soup = BeautifulSoup(html, 'html.parser')
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
    soup = BeautifulSoup(html, 'html.parser')
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
    soup = BeautifulSoup(html, 'html.parser')
    equipment = parser._parse_equipment(soup, {})
    
    assert len(equipment) > 0
    assert all(hasattr(eq, 'slot') for eq in equipment)
