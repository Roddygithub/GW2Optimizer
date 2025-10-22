"""
GW2 API Service - Integration with Guild Wars 2 Official API
Fetches live WvW data for team composition optimization
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.logging import logger
from app.core.config import settings


class GW2APIService:
    """Service for interacting with Guild Wars 2 API"""
    
    BASE_URL = "https://api.guildwars2.com/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GW2 API service.
        
        Args:
            api_key: GW2 API key (optional, required for authenticated endpoints)
        """
        self.api_key = api_key or getattr(settings, 'GW2_API_KEY', None)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GW2 API.
        
        Args:
            endpoint: API endpoint (e.g., "/wvw/matches")
            params: Query parameters
            authenticated: Whether to include API key
        
        Returns:
            JSON response data
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}
        
        if authenticated and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"GW2 API request failed: {endpoint} - {str(e)}")
            raise
    
    async def get_wvw_matches(self, world_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get current WvW matches.
        
        Args:
            world_id: Optional world ID to filter matches
        
        Returns:
            List of WvW match data
        """
        params = {"world": world_id} if world_id else None
        return await self._make_request("/wvw/matches", params=params)
    
    async def get_wvw_match_details(self, match_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific WvW match.
        
        Args:
            match_id: Match ID
        
        Returns:
            Match details including scores and objectives
        """
        return await self._make_request(f"/wvw/matches/{match_id}")
    
    async def get_wvw_objectives(self) -> List[Dict[str, Any]]:
        """
        Get all WvW objectives (keeps, towers, camps, etc.).
        
        Returns:
            List of WvW objectives
        """
        return await self._make_request("/wvw/objectives")
    
    async def fetch_live_wvw_data(self, world_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch comprehensive live WvW data for team composition analysis.
        
        Args:
            world_id: Optional world ID to focus on
        
        Returns:
            Comprehensive WvW data including matches, scores, and objectives
        """
        logger.info(f"🌐 Fetching live WvW data from GW2 API (world_id: {world_id})")
        
        try:
            # Get current matches
            matches = await self.get_wvw_matches(world_id)
            
            # Get detailed match data for first match
            match_details = None
            if matches:
                match_id = matches[0].get("id")
                if match_id:
                    match_details = await self.get_wvw_match_details(match_id)
            
            # Get objectives
            objectives = await self.get_wvw_objectives()
            
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "world_id": world_id,
                "matches": matches,
                "match_details": match_details,
                "objectives": objectives,
                "status": "success"
            }
            
            logger.info(f"✅ Successfully fetched WvW data: {len(matches)} matches")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch WvW data: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "world_id": world_id,
                "status": "error",
                "error": str(e)
            }
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get authenticated account information.
        
        Requires API key with 'account' permission.
        
        Returns:
            Account information
        """
        if not self.api_key:
            raise ValueError("API key required for account information")
        
        return await self._make_request("/account", authenticated=True)
    
    async def get_characters(self) -> List[str]:
        """
        Get list of character names for authenticated account.
        
        Requires API key with 'characters' permission.
        
        Returns:
            List of character names
        """
        if not self.api_key:
            raise ValueError("API key required for characters")
        
        return await self._make_request("/characters", authenticated=True)


# Singleton instance
_gw2_api_service: Optional[GW2APIService] = None


def get_gw2_api_service() -> GW2APIService:
    """Get or create GW2 API service instance"""
    global _gw2_api_service
    if _gw2_api_service is None:
        _gw2_api_service = GW2APIService()
    return _gw2_api_service
