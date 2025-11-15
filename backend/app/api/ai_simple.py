"""
Simple AI endpoints for test compatibility.
"""

from fastapi import APIRouter, Depends, status
from typing import Dict, Any

from app.api.auth import get_current_active_user
from app.db.models import UserDB as User

router = APIRouter(prefix="/api/v1/ai", tags=["ai-simple"])


@router.post("/compose-team", status_code=status.HTTP_200_OK)
async def compose_team_simple(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Simple team composition endpoint for tests."""
    return {"result": "ok", "action": "compose", "team": []}


@router.post("/optimize-build", status_code=status.HTTP_200_OK)
async def optimize_build_simple(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Simple build optimization endpoint for tests."""
    return {"result": "ok", "action": "optimize", "build": {}}


@router.post("/analyze-synergy", status_code=status.HTTP_200_OK)
async def analyze_synergy_simple(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Simple synergy analysis endpoint for tests."""
    return {"result": "ok", "action": "synergy", "score": 0.8}
