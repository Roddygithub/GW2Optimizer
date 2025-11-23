"""Proof-of-concept tests for AI logic on GW2 skills.

This validates the end-to-end flow:
- Fetch skill details from GW2 API client
- Analyze the skill with the AnalystAgent (via OllamaService)
- Return a structured analysis result

All external calls (GW2 API, Mistral) are fully mocked.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.skill_analysis_service import SkillAnalysisService


pytestmark = pytest.mark.asyncio


async def test_skill_analysis_flow_end_to_end():
    """End-to-end logic: GW2 skill -> LLM analysis -> structured result.

    This is a pure PoC test: it ensures we can plug real GW2 data
    into the AI layer without doing real network calls.
    """

    fake_skill = {
        "id": 12345,
        "name": "Symbol of Swiftness",
        "description": "Create a symbol that grants swiftness to allies.",
        "professions": ["Guardian"],
        "slot": "Weapon_2",
        "type": "Weapon",
    }

    async_mock_get_skill = AsyncMock(return_value=fake_skill)
    async_mock_generate = AsyncMock(
        return_value={
            "rating": "Méta",
            "reason": "C'est un très bon sort de support en WvW zerg.",
            "tags": ["support", "zerg", "boons"],
        }
    )

    with patch("app.services.gw2_api_client.GW2APIClient.get_skill_details", async_mock_get_skill), patch(
        "app.services.ai.ollama_service.OllamaService.generate_structured", async_mock_generate
    ):
        service = SkillAnalysisService()

        result = await service.analyze_skill(12345, context="WvW Zerg Support")

        async_mock_get_skill.assert_awaited_once_with(12345)
        async_mock_generate.assert_awaited_once()

        args, kwargs = async_mock_generate.call_args
        prompt = kwargs.get("prompt") or (args[0] if args else "")
        assert "Symbol of Swiftness" in prompt
        assert "WvW Zerg Support" in prompt

        assert result["skill_id"] == 12345
        assert result["skill_name"] == "Symbol of Swiftness"
        assert result["rating"] == "Méta"
        assert "support" in result["tags"]
        assert "zerg" in result["tags"]
