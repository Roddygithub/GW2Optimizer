"""
Interaction data collector for learning.

Collects anonymous user interactions with builds and teams for future ML training.
All data is stored locally and can be automatically purged.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.logging import logger
from app.learning.data.storage import LearningStorage


class InteractionType:
    """Types of user interactions to collect."""

    BUILD_CREATED = "build_created"
    BUILD_UPDATED = "build_updated"
    BUILD_DELETED = "build_deleted"
    BUILD_VIEWED = "build_viewed"
    TEAM_CREATED = "team_created"
    TEAM_UPDATED = "team_updated"
    TEAM_DELETED = "team_deleted"
    TEAM_VIEWED = "team_viewed"
    BUILD_RATED = "build_rated"
    TEAM_RATED = "team_rated"


class InteractionCollector:
    """
    Collector for user interaction data.

    Collects anonymous interaction data for future machine learning applications.
    All data is stored locally and automatically managed based on configured limits.
    """

    def __init__(self):
        """Initialize the interaction collector."""
        self.storage = LearningStorage()
        self.enabled = settings.LEARNING_ENABLED

        if not self.enabled:
            logger.info("⚠️  Learning data collection is disabled")

    async def collect_interaction(
        self,
        interaction_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Collect a user interaction.

        Args:
            interaction_type: Type of interaction (from InteractionType)
            data: Interaction data (anonymized)
            user_id: Optional anonymized user ID
            metadata: Optional additional metadata

        Returns:
            True if collected successfully, False otherwise

        Example:
            await collector.collect_interaction(
                InteractionType.BUILD_CREATED,
                {
                    "profession": "Guardian",
                    "game_mode": "zerg",
                    "role": "support"
                },
                user_id="anon_user_123"
            )
        """
        if not self.enabled:
            return False

        try:
            interaction = {
                "id": str(uuid4()),
                "type": interaction_type,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id or "anonymous",
                "data": data,
                "metadata": metadata or {},
            }

            return await self.storage.store_interaction(interaction)

        except Exception as e:
            logger.error(f"❌ Error collecting interaction: {e}")
            return False

    async def collect_build_creation(self, build_data: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """
        Collect build creation event.

        Args:
            build_data: Build data (anonymized)
            user_id: Optional anonymized user ID

        Returns:
            True if collected successfully
        """
        # Anonymize build data (remove personal info)
        anonymous_data = {
            "profession": build_data.get("profession"),
            "game_mode": build_data.get("game_mode"),
            "role": build_data.get("role"),
            "specialization": build_data.get("specialization"),
            "source_type": build_data.get("source_type"),
            "has_trait_lines": bool(build_data.get("trait_lines")),
            "has_skills": bool(build_data.get("skills")),
            "has_equipment": bool(build_data.get("equipment")),
        }

        return await self.collect_interaction(InteractionType.BUILD_CREATED, anonymous_data, user_id)

    async def collect_team_creation(self, team_data: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """
        Collect team creation event.

        Args:
            team_data: Team data (anonymized)
            user_id: Optional anonymized user ID

        Returns:
            True if collected successfully
        """
        # Anonymize team data
        anonymous_data = {
            "game_mode": team_data.get("game_mode"),
            "team_size": team_data.get("team_size"),
            "build_count": len(team_data.get("build_ids", [])),
            "has_synergies": bool(team_data.get("synergies")),
        }

        return await self.collect_interaction(InteractionType.TEAM_CREATED, anonymous_data, user_id)

    async def collect_build_rating(self, build_id: str, rating: float, user_id: Optional[str] = None) -> bool:
        """
        Collect build rating event.

        Args:
            build_id: Build ID (anonymized)
            rating: Rating value
            user_id: Optional anonymized user ID

        Returns:
            True if collected successfully
        """
        anonymous_data = {
            "build_id_hash": hash(build_id),  # Anonymized ID
            "rating": rating,
        }

        return await self.collect_interaction(InteractionType.BUILD_RATED, anonymous_data, user_id)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get collection statistics.

        Returns:
            Dictionary with collection statistics
        """
        return await self.storage.get_statistics()

    async def purge_old_data(self, days: int = 90) -> int:
        """
        Purge interaction data older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of records purged
        """
        return await self.storage.purge_old_data(days)
