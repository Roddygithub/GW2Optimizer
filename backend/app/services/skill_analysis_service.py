from typing import Any, Dict, Optional

from app.core.logging import logger
from app.services.gw2_api_client import GW2APIClient
from app.agents.analyst_agent import AnalystAgent


class SkillAnalysisService:
    def __init__(
        self,
        gw2_client: Optional[GW2APIClient] = None,
        analyst_agent: Optional[AnalystAgent] = None,
    ) -> None:
        self.gw2_client = gw2_client or GW2APIClient()
        self.analyst_agent = analyst_agent or AnalystAgent()

    async def analyze_skill(self, skill_id: int, context: str = "WvW Zerg") -> Dict[str, Any]:
        logger.info(f"Analyzing GW2 skill {skill_id} for context {context}")
        skill_data = await self.gw2_client.get_skill_details(skill_id)
        if not skill_data:
            raise ValueError(f"Skill {skill_id} not found")

        envelope = await self.analyst_agent.execute({"skill_data": skill_data, "context": context})
        if not envelope.get("success"):
            error = envelope.get("error") or "unknown_error"
            raise RuntimeError(f"AnalystAgent failed: {error}")

        return envelope["result"]
