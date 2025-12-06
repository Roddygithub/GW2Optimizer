"""
API Endpoints for Team Commander Agent.
Route: /api/v1/ai/teams/*
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_active_user
from app.db.models import UserDB as User
from app.agents.team_commander_agent import get_team_commander, TeamResult
from app.core.logging import logger
from app.models.learning import DataSource
from app.services.learning.data_collector import DataCollector
from app.services.gear_preset_service import get_gear_preset_service


router = APIRouter(tags=["AI Team Commander"])
collector = DataCollector()


class TeamCommandRequest(BaseModel):
    """Request body for team command."""
    message: str
    experience: Optional[str] = None
    mode: Optional[str] = None


class TeamCommandResponse(BaseModel):
    """Response for team command."""
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None


@router.post("/command", response_model=Dict[str, Any])
async def command_team(
    request: TeamCommandRequest,
    # Temporarily disable authentication for testing
    # current_user: User = Depends(get_current_active_user),
):
    # Create a mock user for testing
    from unittest.mock import MagicMock
    current_user = MagicMock()
    current_user.id = 1
    current_user.username = "test_user"
    try:
        logger.info(f"🎮 Team command from user {current_user.id}: {request.message[:100]}...")
        
        # Get agent
        agent = get_team_commander()

        # Run command (experience permet d'ajuster le curseur de skill level, mode ajuste le contexte WvW)
        result: TeamResult = await agent.run(
            request.message,
            experience=request.experience,
            mode=request.mode,
        )

        # Préparer un petit cache local pour les presets d'armure par préfixe
        preset_service = get_gear_preset_service()
        armor_cache: Dict[str, Any] = {}

        # Format response
        response = {
            "success": True,
            "team_size": sum(len(g.slots) for g in result.groups),
            "groups": [
                {
                    "index": group.index,
                    "slots": [
                        {
                            "role": slot.role.value,
                            "profession": slot.profession,
                            "specialization": slot.specialization,
                            "gear_mix": getattr(slot, "gear_mix", None),
                            "equipment": (
                                lambda stats_priority=slot.stats_priority: {
                                    "stats": stats_priority,
                                    "rune": slot.rune,
                                    "sigils": slot.sigils,
                                    "relic": getattr(slot, "relic", None),
                                    "example_armor": armor_cache.get(stats_priority),
                                }
                            )(),
                            "performance": slot.performance,
                            "advisor_reason": getattr(slot, "advisor_reason", None),
                            "advisor_alternatives": getattr(slot, "advisor_alternatives", None),
                        }
                        for slot in group.slots
                    ],
                }
                for group in result.groups
            ],
            "synergy": {
                "score": result.synergy_score,
                "details": result.synergy_details,
            },
            "notes": result.notes,
        }

        # Remplir example_armor dans le cache après avoir construit la structure de base
        try:
            for group in response["groups"]:
                for slot in group["slots"]:
                    stats_priority = slot["equipment"].get("stats")
                    if not isinstance(stats_priority, str) or not stats_priority:
                        continue
                    if stats_priority in armor_cache:
                        slot["equipment"]["example_armor"] = armor_cache[stats_priority]
                        continue
                    armor_items = preset_service.get_example_armor_for_prefix(stats_priority)
                    if armor_items:
                        serialized = [item.model_dump() for item in armor_items]
                    else:
                        serialized = []
                    armor_cache[stats_priority] = serialized
                    slot["equipment"]["example_armor"] = serialized
        except Exception:
            # Ne jamais casser la réponse si les presets d'armure échouent
            pass
        
        logger.info(f"✅ Team command success: {result.synergy_score} synergy")
        try:
            mode_val = request.mode or "wvw_zerg"
            game_mode_for_learning = mode_val.lower().replace("wvw_", "")
            team_data = {
                "game_mode": game_mode_for_learning,
                "team_size": response.get("team_size"),
                "groups": response.get("groups", []),
                "synergy": response.get("synergy", {}),
                "notes": response.get("notes", []),
                "source": "team_commander",
                "user_message": request.message,
            }
            await collector.collect_team_from_dict(
                team_data=team_data,
                game_mode=game_mode_for_learning,
                source=DataSource.AI_GENERATED,
            )
        except Exception as e:
            logger.warning("Failed to collect TeamCommander team for learning", extra={"error": str(e)})
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Team command failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build team: {str(e)}"
        )


@router.get("/templates")
async def get_team_templates(
    current_user: User = Depends(get_current_active_user),
):
    """
    Retourne des templates de teams WvW prédéfinis.
    
    Utile pour donner des exemples à l'utilisateur.
    """
    templates = [
        {
            "name": "Zerg Standard",
            "description": "2 groupes de 5 - Composition classique pour zerg WvW",
            "command": "2 groupes de 5 avec Firebrand, Druid, Herald, Spellbreaker, Reaper",
        },
        {
            "name": "Outnumber Squad",
            "description": "Petit groupe optimisé pour outnumber (5v15+)",
            "command": "1 groupe de 5 avec Firebrand, Spellbreaker, Deadeye, Holosmith, Willbender",
        },
        {
            "name": "Roaming Party",
            "description": "Petit groupe mobile pour roaming",
            "command": "1 groupe de 5 avec Spellbreaker, Willbender, Deadeye, Scrapper, Herald",
        },
    ]
    
    return {"templates": templates}
