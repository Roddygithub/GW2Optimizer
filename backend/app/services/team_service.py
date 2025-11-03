"""Team composition service."""

import uuid
from typing import List, Optional

from app.core.logging import logger
from app.models.build import GameMode
from app.models.learning import DataSource
from app.models.team import (
    TeamComposition,
    TeamOptimizeRequest,
    TeamResponse,
    TeamSynergy,
)
from app.services.ai.ollama_service import OllamaService
from app.services.learning.data_collector import DataCollector
from app.services.synergy_analyzer import SynergyAnalyzer


class TeamService:
    """Service for managing team compositions."""

    def __init__(self) -> None:
        """Initialize team service."""
        self.ollama = OllamaService()
        self.collector = DataCollector()
        self.analyzer = SynergyAnalyzer()
        self.teams_cache: dict[str, TeamComposition] = {}

    async def optimize_team(self, request: TeamOptimizeRequest) -> TeamResponse:
        """Optimize a team composition."""
        try:
            team = await self._generate_team_with_ai(request)
            synergies = await self._analyze_synergies(team)
            team.synergies = synergies

            ai_recommendations = await self._generate_recommendations(team)
            alternatives = await self._generate_alternatives(request)

            if not team.id:
                team.id = str(uuid.uuid4())
            self.teams_cache[team.id] = team

            # Collect for learning
            try:
                await self.collector.collect_team(team, DataSource.AI_GENERATED)
            except Exception as e:
                logger.warning(f"Failed to collect team for learning: {e}")

            return TeamResponse(
                team=team,
                ai_recommendations=ai_recommendations,
                alternative_compositions=alternatives,
            )
        except Exception as e:
            logger.error(f"Error optimizing team: {e}")
            raise

    async def get_team(self, team_id: str) -> Optional[TeamComposition]:
        """Get team by ID."""
        return self.teams_cache.get(team_id)

    async def list_teams(self, game_mode: Optional[GameMode] = None, limit: int = 20) -> List[TeamComposition]:
        """List teams with filters."""
        teams = list(self.teams_cache.values())
        if game_mode:
            teams = [t for t in teams if t.game_mode == game_mode]
        return teams[:limit]

    async def analyze_team(self, team: TeamComposition) -> TeamResponse:
        """Analyze an existing team."""
        synergies = await self._analyze_synergies(team)
        team.synergies = synergies
        ai_recommendations = await self._generate_recommendations(team)
        return TeamResponse(team=team, ai_recommendations=ai_recommendations)

    async def _generate_team_with_ai(self, request: TeamOptimizeRequest) -> TeamComposition:
        """Generate team composition using AI."""
        prompt = f"""Generate optimal {request.team_size}-player {request.game_mode.value} WvW team.
Roles: {request.required_roles or "Balanced"}
Constraints: {request.constraints or "None"}"""

        response = await self.ollama.generate(prompt, temperature=0.6)

        return TeamComposition(
            id=str(uuid.uuid4()),
            name=f"{request.game_mode.value.title()} Team ({request.team_size})",
            game_mode=request.game_mode,
            team_size=request.team_size,
            description=response,
            created_by="ai",
        )

    async def _analyze_synergies(self, team: TeamComposition) -> List[TeamSynergy]:
        """Analyze team synergies using advanced analyzer."""
        if not team.slots:
            return []

        # Use synergy analyzer for detailed analysis
        synergies = self.analyzer.analyze_team(team)

        # Calculate team scores
        scores = self.analyzer.calculate_team_score(team)
        team.overall_rating = scores.get("overall", 5.0)

        # Add strengths and weaknesses based on scores
        team.strengths = []
        team.weaknesses = []

        if scores.get("boon_coverage", 0) >= 8:
            team.strengths.append("Excellent boon coverage")
        elif scores.get("boon_coverage", 0) < 5:
            team.weaknesses.append("Insufficient boon coverage")

        if scores.get("role_balance", 0) >= 8:
            team.strengths.append("Well-balanced roles")
        elif scores.get("role_balance", 0) < 5:
            team.weaknesses.append("Poor role distribution")

        if scores.get("survivability", 0) >= 8:
            team.strengths.append("High survivability")
        elif scores.get("survivability", 0) < 5:
            team.weaknesses.append("Low survivability")

        return synergies

    async def _generate_recommendations(self, team: TeamComposition) -> dict[str, str]:
        """Generate AI recommendations."""
        prompt = f"Recommend improvements for {team.game_mode.value} team: {team.name}"
        response = await self.ollama.generate(prompt, temperature=0.6)
        return {"recommendations": response, "team_name": team.name}

    async def _generate_alternatives(self, request: TeamOptimizeRequest) -> List[TeamComposition]:
        """Generate alternative compositions."""
        return []
