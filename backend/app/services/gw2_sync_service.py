"""GW2 API synchronization service."""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, cast

import aiohttp
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.base_class import Base
from app.models.gw2.entities import (
    Build,
    Item,
    Profession,
    Skill,
    Specialization,
    Trait,
    Weapon,
)

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)

# Base URL for the GW2 API
GW2_API_BASE_URL = "https://api.guildwars2.com/v2"

# Rate limiting constants
RATE_LIMIT = 300  # GW2 API rate limit (requests per minute)
REQUEST_DELAY = 60 / RATE_LIMIT  # Delay between requests in seconds

# Headers for API requests
HEADERS = {
    "User-Agent": f"GW2Optimizer/{settings.VERSION} (https://github.com/YourUsername/GW2Optimizer)",
    "Accept": "application/json",
}


class GW2SyncService:
    """Service for synchronizing GW2 API data with the local database."""

    def __init__(self, db: AsyncSession):
        """Initialize the sync service with a database session."""
        self.db = db
        self.session = None
        self.last_request_time = 0

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=HEADERS)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make a request to the GW2 API with rate limiting and error handling."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async with GW2SyncService()")

        # Enforce rate limiting
        now = datetime.now().timestamp()
        time_since_last = now - self.last_request_time
        if time_since_last < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - time_since_last)

        url = f"{GW2_API_BASE_URL}/{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                self.last_request_time = datetime.now().timestamp()
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.warning(f"Resource not found: {url}")
                    return None
                elif response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)
                else:
                    error_text = await response.text()
                    logger.error(
                        f"API request failed: {response.status} - {error_text}"
                    )
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"Error making API request to {url}: {e}")
            return None

    async def _get_or_create(
        self, model: Type[ModelType], id: Any, **kwargs
    ) -> ModelType:
        """Get an instance or create it if it doesn't exist."""
        instance = await self.db.get(model, id)
        if not instance:
            instance = model(id=id, **kwargs)
            self.db.add(instance)
        return instance

    async def _update_or_create(
        self, model: Type[ModelType], id: Any, **kwargs
    ) -> ModelType:
        """Update an instance or create it if it doesn't exist."""
        instance = await self.db.get(model, id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
        else:
            instance = model(id=id, **kwargs)
            self.db.add(instance)
        return instance

    async def sync_all(self):
        """Synchronize all GW2 data."""
        logger.info("Starting full GW2 data synchronization...")
        
        # Sync professions first as other entities depend on them
        await self.sync_professions()
        
        # Sync other entities in parallel
        await asyncio.gather(
            self.sync_specializations(),
            self.sync_skills(),
            self.sync_traits(),
            self.sync_items(),
            self.sync_weapons(),
        )
        
        # Builds are handled separately as they're user-created
        logger.info("GW2 data synchronization complete!")

    async def sync_professions(self) -> List[Profession]:
        """Synchronize professions from the GW2 API."""
        logger.info("Synchronizing professions...")
        
        # Get all profession IDs
        profession_ids = await self._make_request("professions")
        if not profession_ids:
            logger.error("Failed to fetch profession IDs")
            return []
            
        # Process each profession
        professions = []
        for prof_id in profession_ids:
            profession_data = await self._make_request(f"professions/{prof_id}")
            if not profession_data:
                continue
                
            # Create or update the profession
            profession = await self._update_or_create(
                Profession,
                id=profession_data["id"],
                name=profession_data["name"],
                description=profession_data.get("description", ""),
                icon=profession_data.get("icon"),
                code=profession_data.get("id"),  # Using the same ID as code for now
                primary_attributes={
                    "weapons": profession_data.get("weapons", {}),
                    "skills": profession_data.get("skills", []),
                },
            )
            professions.append(profession)
            
        await self.db.commit()
        logger.info(f"Synchronized {len(professions)} professions")
        return professions

    async def sync_specializations(self) -> List[Specialization]:
        """Synchronize specializations from the GW2 API."""
        logger.info("Synchronizing specializations...")
        
        # Get all specialization IDs
        spec_ids = await self._make_request("specializations")
        if not spec_ids:
            logger.error("Failed to fetch specialization IDs")
            return []
            
        # Process each specialization
        specializations = []
        for spec_id in spec_ids:
            spec_data = await self._make_request(f"specializations/{spec_id}")
            if not spec_data:
                continue
                
            # Get the profession for this specialization
            profession = await self.db.execute(
                select(Profession).where(Profession.code == spec_data["profession"])
            )
            profession = profession.scalar_one_or_none()
            
            if not profession:
                logger.warning(
                    f"Skipping specialization {spec_data['name']} - "
                    f"Profession {spec_data['profession']} not found"
                )
                continue
                
            # Create or update the specialization
            specialization = await self._update_or_create(
                Specialization,
                id=spec_data["id"],
                name=spec_data["name"],
                description=spec_data.get("background", ""),
                icon=spec_data.get("icon"),
                elite=spec_data.get("elite", False),
                profession_id=profession.id,
                minor_traits=spec_data.get("minor_traits", []),
                major_traits=spec_data.get("major_traits", []),
            )
            specializations.append(specialization)
            
        await self.db.commit()
        logger.info(f"Synchronized {len(specializations)} specializations")
        return specializations

    async def sync_skills(self) -> List[Skill]:
        """Synchronize skills from the GW2 API."""
        logger.info("Synchronizing skills...")
        
        # Get all skill IDs
        skill_ids = await self._make_request("skills")
        if not skill_ids:
            logger.error("Failed to fetch skill IDs")
            return []
            
        # Process each skill
        skills = []
        for skill_id in skill_ids:
            skill_data = await self._make_request(f"skills/{skill_id}")
            if not skill_data:
                continue
                
            # Get the profession for this skill if specified
            profession_id = None
            if "professions" in skill_data and skill_data["professions"]:
                profession = await self.db.execute(
                    select(Profession).where(Profession.code == skill_data["professions"][0])
                )
                profession = profession.scalar_one_or_none()
                if profession:
                    profession_id = profession.id
            
            # Determine skill type
            skill_type = "utility"  # Default
            if skill_data.get("slot") == "Weapon":
                skill_type = "weapon"
            elif skill_data.get("slot") == "Heal":
                skill_type = "heal"
            elif skill_data.get("slot") == "Elite":
                skill_type = "elite"
                
            # Create or update the skill
            skill = await self._update_or_create(
                Skill,
                id=skill_data["id"],
                name=skill_data["name"],
                description=skill_data.get("description", ""),
                icon=skill_data.get("icon"),
                type=skill_type,
                weapon_type=skill_data.get("weapon_type"),
                profession_id=profession_id,
            )
            skills.append(skill)
            
        await self.db.commit()
        logger.info(f"Synchronized {len(skills)} skills")
        return skills

    async def sync_traits(self) -> List[Trait]:
        """Synchronize traits from the GW2 API."""
        logger.info("Synchronizing traits...")
        
        # Get all trait IDs
        trait_ids = await self._make_request("traits")
        if not trait_ids:
            logger.error("Failed to fetch trait IDs")
            return []
            
        # Process each trait
        traits = []
        for trait_id in trait_ids:
            trait_data = await self._make_request(f"traits/{trait_id}")
            if not trait_data:
                continue
                
            # Get the specialization for this trait
            specialization = None
            if "specialization" in trait_data:
                specialization = await self.db.execute(
                    select(Specialization).where(Specialization.id == trait_data["specialization"])
                )
                specialization = specialization.scalar_one_or_none()
            
            if not specialization:
                logger.warning(
                    f"Skipping trait {trait_data['name']} - "
                    f"Specialization {trait_data.get('specialization')} not found"
                )
                continue
                
            # Determine trait slot
            slot = "adept"  # Default
            if "slot" in trait_data and trait_data["slot"]:
                slot = trait_data["slot"].lower()
                
            # Create or update the trait
            trait = await self._update_or_create(
                Trait,
                id=trait_data["id"],
                name=trait_data["name"],
                description=trait_data.get("description", ""),
                icon=trait_data.get("icon"),
                slot=slot,
                specialization_id=specialization.id,
                variables=trait_data.get("facts", []) + trait_data.get("traited_facts", []),
            )
            traits.append(trait)
            
        await self.db.commit()
        logger.info(f"Synchronized {len(traits)} traits")
        return traits

    async def sync_items(self) -> List[Item]:
        """Synchronize items from the GW2 API."""
        logger.info("Synchronizing items...")
        
        # Get all item IDs (this might be a large list, consider pagination in production)
        item_ids = await self._make_request("items")
        if not item_ids:
            logger.error("Failed to fetch item IDs")
            return []
            
        # Process each item (in production, you'd want to batch these)
        items = []
        for item_id in item_ids[:100]:  # Limit to first 100 for testing
            item_data = await self._make_request(f"items/{item_id}")
            if not item_data:
                continue
                
            # Skip items that aren't relevant to builds (armor, trinkets, weapons, consumables)
            item_type = item_data.get("type", "").lower()
            if item_type not in ["armor", "trinket", "weapon", "consumable"]:
                continue
                
            # Map GW2 item type to our internal type
            mapped_type = item_type
            if item_type == "consumable" and item_data.get("details", {}).get("type") == "Food":
                mapped_type = "food"
            elif item_type == "consumable" and item_data.get("details", {}).get("type") == "Utility":
                mapped_type = "utility"
                
            # Create or update the item
            item = await self._update_or_create(
                Item,
                id=item_data["id"],
                name=item_data["name"],
                description=item_data.get("description", ""),
                icon=item_data.get("icon"),
                type=mapped_type,
                rarity=item_data.get("rarity"),
                stats_json=item_data.get("details", {}).get("infix_upgrade", {}).get("buff", {})
            )
            items.append(item)
            
        await self.db.commit()
        logger.info(f"Synchronized {len(items)} items")
        return items

    async def sync_weapons(self) -> List[Weapon]:
        """Synchronize weapons from the GW2 API."""
        logger.info("Synchronizing weapons...")
        
        # Get all weapon IDs
        weapon_ids = await self._make_request("weapons")
        if not weapon_ids:
            logger.error("Failed to fetch weapon IDs")
            return []
            
        # Process each weapon
        weapons = []
        for weapon_id in weapon_ids:
            weapon_data = await self._make_request(f"weapons/{weapon_id}")
            if not weapon_data:
                continue
                
            # Create or update the weapon
            weapon = await self._update_or_create(
                Weapon,
                id=weapon_data["id"],
                name=weapon_data["name"],
                description=weapon_data.get("description", ""),
                icon=weapon_data.get("icon"),
                type=weapon_data.get("type", ""),
                two_handed=weapon_data.get("details", {}).get("type") == "TwoHand",
            )
            
            # Update weapon skills if they exist
            if "skills" in weapon_data and weapon_data["skills"]:
                skill_ids = [skill["id"] for skill in weapon_data["skills"] if "id" in skill]
                if skill_ids:
                    skills = await self.db.execute(
                        select(Skill).where(Skill.id.in_(skill_ids))
                    )
                    weapon.skills = skills.scalars().all()
            
            weapons.append(weapon)
            
        await self.db.commit()
        logger.info(f"Synchronized {len(weapons)} weapons")
        return weapons


async def sync_gw2_data(db: AsyncSession):
    """Convenience function to sync all GW2 data.
    
    Args:
        db: The database session to use for the sync.
        
    Returns:
        The result of the sync operation, which is the result of sync_all().
    """
    async with GW2SyncService(db) as sync_service:
        return await sync_service.sync_all()
