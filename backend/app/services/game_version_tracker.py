"""Service to track GW2 game version and balance patches for auto-updates."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
from app.core.logging import logger
from app.core.config import settings


class GameVersionTracker:
    """Track Guild Wars 2 game version and balance patches."""

    # GW2 API endpoints
    BUILD_API = "https://api.guildwars2.com/v2/build"
    
    # ArenaNet news/changelog (for detecting balance patches)
    PATCH_NOTES_URL = "https://en-forum.guildwars2.com/categories/game-release-notes"
    
    def __init__(self):
        self.current_build: Optional[int] = None
        self.last_check: Optional[datetime] = None
        # Check every Tuesday at 19:00 (once per week)
        self.check_day = 1  # 0=Monday, 1=Tuesday, etc.
        self.check_hour = 19
        self.last_known_balance_patch: Optional[str] = None

    async def get_current_game_build(self) -> Optional[int]:
        """
        Fetch current GW2 game build number from official API.

        Returns:
            Current build number or None if request fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BUILD_API)
                response.raise_for_status()
                data = response.json()
                
                build_id = data.get("id")
                logger.info(f"Fetched GW2 build: {build_id}")
                return build_id
                
        except Exception as e:
            logger.error(f"Failed to fetch GW2 build: {e}")
            return None

    async def check_for_game_update(self) -> Dict[str, Any]:
        """
        Check if there's a new game build.

        Returns:
            Dictionary with:
                - has_update: bool
                - old_build: int or None
                - new_build: int or None
                - message: str
        """
        new_build = await self.get_current_game_build()
        
        if new_build is None:
            return {
                "has_update": False,
                "old_build": self.current_build,
                "new_build": None,
                "message": "Failed to fetch game build",
            }
        
        if self.current_build is None:
            # First time checking
            self.current_build = new_build
            self.last_check = datetime.utcnow()
            return {
                "has_update": False,
                "old_build": None,
                "new_build": new_build,
                "message": f"Initial build recorded: {new_build}",
            }
        
        has_update = new_build > self.current_build
        
        if has_update:
            logger.warning(
                f"🔄 GW2 game update detected! Old build: {self.current_build}, New build: {new_build}"
            )
            old = self.current_build
            self.current_build = new_build
            self.last_check = datetime.utcnow()
            
            return {
                "has_update": True,
                "old_build": old,
                "new_build": new_build,
                "message": f"Game updated from build {old} to {new_build}",
                "action_required": "Review damage formulas and stat constants",
            }
        
        self.last_check = datetime.utcnow()
        return {
            "has_update": False,
            "old_build": self.current_build,
            "new_build": new_build,
            "message": "No game update detected",
        }

    def should_check_for_update(self) -> bool:
        """Check if it's Tuesday 19:00 and we haven't checked this week."""
        now = datetime.utcnow()
        
        # First time check
        if self.last_check is None:
            return True
        
        # Check if it's Tuesday and after 19:00
        is_tuesday = now.weekday() == self.check_day
        is_after_check_hour = now.hour >= self.check_hour
        
        # Check if we already checked this week
        days_since_last = (now - self.last_check).days
        already_checked_this_week = days_since_last < 7
        
        return is_tuesday and is_after_check_hour and not already_checked_this_week

    async def detect_balance_patch_heuristic(self) -> Dict[str, Any]:
        """
        Heuristic check for balance patches (skill/trait changes).

        This checks for significant changes in skill coefficients or new traits.
        In production, you'd want to scrape patch notes or track skill API changes.

        Returns:
            Dictionary with:
                - potential_balance_patch: bool
                - confidence: str
                - message: str
        """
        # TODO: Implement more sophisticated balance patch detection
        # Options:
        # 1. Scrape ArenaNet patch notes
        # 2. Compare skill coefficients from GW2 API over time
        # 3. Monitor specific skills/traits for changes
        
        logger.info("Balance patch detection not yet implemented (placeholder)")
        
        return {
            "potential_balance_patch": False,
            "confidence": "low",
            "message": "Balance patch detection requires implementation",
            "recommendation": "Manually review patch notes at https://en-forum.guildwars2.com/",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current tracking status."""
        return {
            "current_build": self.current_build,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "next_check_in": str(self.check_interval - (datetime.utcnow() - self.last_check))
            if self.last_check
            else "Now",
            "check_interval_hours": self.check_interval.total_seconds() / 3600,
        }


# Global singleton
_tracker_instance: Optional[GameVersionTracker] = None


def get_version_tracker() -> GameVersionTracker:
    """Get or create the global version tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = GameVersionTracker()
    return _tracker_instance


async def periodic_version_check_task():
    """Background task to periodically check for game updates."""
    tracker = get_version_tracker()
    
    while True:
        try:
            if tracker.should_check_for_update():
                result = await tracker.check_for_game_update()
                
                if result["has_update"]:
                    logger.warning(
                        f"🚨 ACTION REQUIRED: GW2 game updated! {result['message']}"
                    )
                    # TODO: Send notification (email, Slack, Discord, etc.)
                    # TODO: Flag engine constants for review
                    # TODO: Re-run validation tests
                
            # Sleep for 1 hour between checks
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in version check task: {e}")
            await asyncio.sleep(3600)  # Continue checking even after errors
