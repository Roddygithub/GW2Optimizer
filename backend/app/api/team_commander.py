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


router = APIRouter(tags=["AI Team Commander"])


class TeamCommandRequest(BaseModel):
    """Request body for team command."""
    message: str


class TeamCommandResponse(BaseModel):
    """Response for team command."""
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None


@router.post("/command", response_model=Dict[str, Any])
async def command_team(
    request: TeamCommandRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Commande IA pour créer une team WvW complète.
    
    L'utilisateur envoie un message en langage naturel, l'IA construit la team.
    
    Exemples de messages:
      - "Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"
      - "Fais-moi une équipe de 10 joueurs avec un stabeur, un healer, un booner, un strip et un dps par groupe"
    
    Args:
        request: TeamCommandRequest avec le message utilisateur
        current_user: Utilisateur authentifié
    
    Returns:
        JSON avec groups, synergy, notes
    """
    try:
        logger.info(f"🎮 Team command from user {current_user.id}: {request.message[:100]}...")
        
        # Get agent
        agent = get_team_commander()
        
        # Run command
        result: TeamResult = await agent.run(request.message)
        
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
                            "equipment": {
                                "stats": slot.stats_priority,
                                "rune": slot.rune,
                                "sigils": slot.sigils,
                            },
                            "performance": slot.performance,
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
        
        logger.info(f"✅ Team command success: {result.synergy_score} synergy")
        
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
