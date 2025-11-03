"""
AI Agent for recommending Guild Wars 2 builds.
"""

import httpx
import json
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.logging import logger


class RecommenderAgent(BaseAgent):
    """
    An agent specialized in generating build recommendations by querying an AI model.
    """

    def __init__(self, model: str = settings.OLLAMA_MODEL, host: str = settings.OLLAMA_HOST):
        self.model = model
        self.host = host

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a build recommendation based on the provided inputs.

        Args:
            inputs: A dictionary containing 'profession', 'role', 'game_mode', and optional 'context'.

        Returns:
            A dictionary containing the build recommendation.
        """
        prompt = f"""
        Based on the game Guild Wars 2, recommend a build for the following specifications:
        - Profession: {inputs.get("profession", "any")}
        - Role: {inputs.get("role", "any")}
        - Game Mode: {inputs.get("game_mode", "any")}
        - Additional Context: {inputs.get("context", "None")}

        Provide a concise build name, a brief description of its playstyle, and a list of key synergies.
        Format the output as a JSON object with the keys "build_name", "description", and "synergies".
        """

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                    },
                )
                response.raise_for_status()
                return json.loads(response.json()["response"])

        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error in RecommenderAgent: {e}")
            raise Exception("Failed to get a recommendation from the AI agent.")
