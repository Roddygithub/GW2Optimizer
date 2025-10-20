"""
Storage manager for learning data.

Manages local storage of interaction data with automatic size management
and GDPR-compliant data handling.
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from app.core.config import settings
from app.core.logging import logger


class LearningStorage:
    """
    Storage manager for learning data.
    
    Handles local storage of interaction data with:
    - Automatic size management
    - Data purging based on age and count
    - JSONL format for efficient append operations
    - Compression for archived data
    """
    
    def __init__(self):
        """Initialize the storage manager."""
        self.data_dir = Path(settings.LEARNING_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.interactions_dir = self.data_dir / "interactions"
        self.interactions_dir.mkdir(exist_ok=True)
        
        self.archive_dir = self.data_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Current interaction file (JSONL format)
        self.current_file = self.interactions_dir / f"interactions_{datetime.utcnow().strftime('%Y%m')}.jsonl"
        
        logger.info(f"✅ Learning storage initialized at {self.data_dir}")

    async def store_interaction(self, interaction: Dict[str, Any]) -> bool:
        """
        Store an interaction to disk.
        
        Args:
            interaction: Interaction data to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Check size limits
            await self._check_size_limits()
            
            # Append to current file (JSONL format)
            async with aiofiles.open(self.current_file, 'a') as f:
                await f.write(json.dumps(interaction) + '\n')
            
            logger.debug(f"Stored interaction: {interaction['type']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing interaction: {e}")
            return False

    async def get_interactions(
        self,
        interaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve interactions from storage.
        
        Args:
            interaction_type: Filter by interaction type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of interactions to return
            
        Returns:
            List of interactions
        """
        interactions = []
        
        try:
            # Read from all JSONL files
            for file_path in sorted(self.interactions_dir.glob("*.jsonl")):
                async with aiofiles.open(file_path, 'r') as f:
                    async for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            interaction = json.loads(line)
                            
                            # Apply filters
                            if interaction_type and interaction.get('type') != interaction_type:
                                continue
                            
                            if start_date:
                                interaction_date = datetime.fromisoformat(interaction['timestamp'])
                                if interaction_date < start_date:
                                    continue
                            
                            if end_date:
                                interaction_date = datetime.fromisoformat(interaction['timestamp'])
                                if interaction_date > end_date:
                                    continue
                            
                            interactions.append(interaction)
                            
                            if len(interactions) >= limit:
                                return interactions
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in {file_path}")
                            continue
            
            return interactions
            
        except Exception as e:
            logger.error(f"❌ Error retrieving interactions: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_interactions = 0
            total_size = 0
            interaction_types = {}
            
            # Count interactions and size
            for file_path in self.interactions_dir.glob("*.jsonl"):
                file_size = file_path.stat().st_size
                total_size += file_size
                
                async with aiofiles.open(file_path, 'r') as f:
                    async for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            interaction = json.loads(line)
                            total_interactions += 1
                            
                            interaction_type = interaction.get('type', 'unknown')
                            interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
                            
                        except json.JSONDecodeError:
                            continue
            
            return {
                "total_interactions": total_interactions,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "interaction_types": interaction_types,
                "data_directory": str(self.data_dir),
                "max_items": settings.MAX_LEARNING_ITEMS,
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}

    async def purge_old_data(self, days: int = 90) -> int:
        """
        Purge interaction data older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records purged
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            purged_count = 0
            
            for file_path in self.interactions_dir.glob("*.jsonl"):
                # Read file and filter
                kept_interactions = []
                
                async with aiofiles.open(file_path, 'r') as f:
                    async for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            interaction = json.loads(line)
                            interaction_date = datetime.fromisoformat(interaction['timestamp'])
                            
                            if interaction_date >= cutoff_date:
                                kept_interactions.append(line)
                            else:
                                purged_count += 1
                                
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
                
                # Rewrite file with kept interactions
                if kept_interactions:
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.writelines(kept_interactions)
                else:
                    # Delete empty file
                    file_path.unlink()
            
            logger.info(f"✅ Purged {purged_count} old interactions (older than {days} days)")
            return purged_count
            
        except Exception as e:
            logger.error(f"❌ Error purging old data: {e}")
            return 0

    async def _check_size_limits(self) -> None:
        """
        Check and enforce size limits.
        
        If the number of interactions exceeds MAX_LEARNING_ITEMS,
        archive the oldest data.
        """
        try:
            stats = await self.get_statistics()
            total_interactions = stats.get('total_interactions', 0)
            
            if total_interactions > settings.MAX_LEARNING_ITEMS:
                # Archive oldest file
                files = sorted(self.interactions_dir.glob("*.jsonl"))
                if files:
                    oldest_file = files[0]
                    archive_path = self.archive_dir / oldest_file.name
                    
                    # Move to archive
                    shutil.move(str(oldest_file), str(archive_path))
                    logger.info(f"✅ Archived {oldest_file.name} to maintain size limits")
                    
        except Exception as e:
            logger.error(f"❌ Error checking size limits: {e}")

    async def clear_all_data(self) -> bool:
        """
        Clear all learning data.
        
        WARNING: This is irreversible!
        
        Returns:
            True if cleared successfully
        """
        try:
            # Clear interactions
            for file_path in self.interactions_dir.glob("*.jsonl"):
                file_path.unlink()
            
            # Clear archive
            for file_path in self.archive_dir.glob("*"):
                file_path.unlink()
            
            logger.warning("⚠️  All learning data cleared")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error clearing data: {e}")
            return False
