"""
Mistral AI Service - Team Composition Generation
Uses Mistral AI to generate optimal team compositions based on WvW data
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.logging import logger
from app.core.config import settings


class MistralAIService:
    """Service for interacting with Mistral AI API"""
    
    API_URL = "https://api.mistral.ai/v1/chat/completions"
    MODEL = "mistral-large-latest"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mistral AI service.
        
        Args:
            api_key: Mistral AI API key
        """
        self.api_key = api_key or getattr(settings, 'MISTRAL_API_KEY', None)
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def generate_team_composition(
        self,
        wvw_data: Dict[str, Any],
        team_size: int = 50,
        game_mode: str = "zerg"
    ) -> Dict[str, Any]:
        """
        Generate optimal team composition using Mistral AI.
        
        Args:
            wvw_data: Live WvW data from GW2 API
            team_size: Desired team size (default: 50 for zerg)
            game_mode: Game mode (zerg, raid, etc.)
        
        Returns:
            Generated team composition with builds and roles
        """
        if not self.api_key:
            logger.warning("⚠️ Mistral API key not configured, using fallback")
            return self._generate_fallback_composition(team_size, game_mode)
        
        logger.info(f"🤖 Generating team composition with Mistral AI (size: {team_size}, mode: {game_mode})")
        
        # Prepare prompt
        prompt = self._create_composition_prompt(wvw_data, team_size, game_mode)
        
        try:
            # Call Mistral AI API
            response = await self.client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert Guild Wars 2 WvW strategist. Generate optimal team compositions based on current match data."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse AI response
            composition = self._parse_ai_response(content, team_size, game_mode)
            
            logger.info(f"✅ Team composition generated successfully")
            return composition
            
        except Exception as e:
            logger.error(f"❌ Mistral AI request failed: {str(e)}")
            return self._generate_fallback_composition(team_size, game_mode)
    
    def _create_composition_prompt(
        self,
        wvw_data: Dict[str, Any],
        team_size: int,
        game_mode: str
    ) -> str:
        """Create prompt for Mistral AI"""
        
        match_info = ""
        if wvw_data.get("match_details"):
            scores = wvw_data["match_details"].get("scores", {})
            match_info = f"Current scores: {scores}"
        
        prompt = f"""
Generate an optimal Guild Wars 2 WvW team composition for {game_mode} mode.

Team Size: {team_size} players
Current Match Data: {match_info}

Requirements:
1. Balanced composition with tanks, supports, and DPS
2. Good boon coverage (might, fury, quickness, alacrity)
3. Strong crowd control capabilities
4. Mobility for map rotations
5. Synergy between professions

Provide the composition in the following JSON format:
{{
    "name": "Team name",
    "size": {team_size},
    "game_mode": "{game_mode}",
    "builds": [
        {{"profession": "Guardian", "role": "Support", "count": X, "priority": "High"}},
        ...
    ],
    "strategy": "Brief strategy description",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"]
}}
"""
        return prompt
    
    def _parse_ai_response(
        self,
        content: str,
        team_size: int,
        game_mode: str
    ) -> Dict[str, Any]:
        """Parse Mistral AI response"""
        
        try:
            # Try to extract JSON from response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                composition = json.loads(json_str)
                
                # Add metadata
                composition["timestamp"] = datetime.utcnow().isoformat()
                composition["source"] = "mistral_ai"
                composition["model"] = self.MODEL
                
                return composition
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return self._generate_fallback_composition(team_size, game_mode)
    
    def _generate_fallback_composition(
        self,
        team_size: int,
        game_mode: str
    ) -> Dict[str, Any]:
        """Generate fallback composition when AI is unavailable"""
        
        logger.info("📋 Generating fallback team composition")
        
        # Standard zerg composition ratios
        composition = {
            "name": f"Standard {game_mode.capitalize()} Composition",
            "size": team_size,
            "game_mode": game_mode,
            "builds": [
                {
                    "profession": "Guardian",
                    "role": "Support",
                    "count": int(team_size * 0.20),  # 20% Guardians
                    "priority": "High",
                    "description": "Firebrand for stability and healing"
                },
                {
                    "profession": "Warrior",
                    "role": "Tank",
                    "count": int(team_size * 0.10),  # 10% Warriors
                    "priority": "High",
                    "description": "Spellbreaker for frontline"
                },
                {
                    "profession": "Necromancer",
                    "role": "DPS",
                    "count": int(team_size * 0.30),  # 30% Necromancers
                    "priority": "High",
                    "description": "Scourge for AoE damage"
                },
                {
                    "profession": "Mesmer",
                    "role": "Support",
                    "count": int(team_size * 0.15),  # 15% Mesmers
                    "priority": "Medium",
                    "description": "Chronomancer for boons and portals"
                },
                {
                    "profession": "Revenant",
                    "role": "DPS",
                    "count": int(team_size * 0.15),  # 15% Revenants
                    "priority": "Medium",
                    "description": "Herald for damage and boons"
                },
                {
                    "profession": "Engineer",
                    "role": "DPS",
                    "count": int(team_size * 0.10),  # 10% Engineers
                    "priority": "Low",
                    "description": "Scrapper for utility"
                },
            ],
            "strategy": "Standard balanced composition for WvW zerg fights",
            "strengths": [
                "Strong boon coverage",
                "Good AoE damage",
                "Excellent stability",
                "Balanced offense and defense"
            ],
            "weaknesses": [
                "Vulnerable to heavy focus fire",
                "Requires good coordination",
                "Limited mobility without portals"
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "source": "fallback",
            "model": "rule_based"
        }
        
        return composition


# Singleton instance
_mistral_service: Optional[MistralAIService] = None


def get_mistral_service() -> MistralAIService:
    """Get or create Mistral AI service instance"""
    global _mistral_service
    if _mistral_service is None:
        _mistral_service = MistralAIService()
    return _mistral_service
