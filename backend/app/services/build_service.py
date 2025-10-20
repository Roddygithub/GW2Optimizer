"""Build service for managing builds."""

import uuid
from typing import List, Optional

from app.core.logging import logger
from app.models.build import Build, BuildCreate, BuildResponse, GameMode, Profession, Role
from app.models.learning import DataSource
from app.services.ai.ollama_service import OllamaService
from app.services.learning.data_collector import DataCollector
from app.services.parser.gw2skill_parser import GW2SkillParser


class BuildService:
    """Service for managing builds."""

    def __init__(self) -> None:
        """Initialize build service."""
        self.ollama = OllamaService()
        self.parser = GW2SkillParser()
        self.collector = DataCollector()
        self.builds_cache: dict[str, Build] = {}

    async def create_build(self, request: BuildCreate) -> BuildResponse:
        """
        Create a new build.

        Args:
            request: Build creation request

        Returns:
            Build response with AI analysis
        """
        try:
            build: Optional[Build] = None

            # If GW2Skill URL provided, parse it
            if request.gw2skill_url:
                build = await self.parser.parse_url(str(request.gw2skill_url))
                if build:
                    # Update with request parameters
                    build.game_mode = request.game_mode
                    build.role = request.role

            # If no build yet, generate with AI
            if not build:
                build = await self._generate_build_with_ai(request)

            # Generate AI analysis
            ai_analysis = await self._analyze_build(build)

            # Find similar builds
            similar_builds = await self._find_similar_builds(build)

            # Store in cache
            if not build.id:
                build.id = str(uuid.uuid4())
            self.builds_cache[build.id] = build

            # Collect for learning (async, no await to not block)
            source = DataSource.PARSED_GW2SKILL if request.gw2skill_url else DataSource.AI_GENERATED
            try:
                await self.collector.collect_build(build, source)
            except Exception as e:
                logger.warning(f"Failed to collect build for learning: {e}")

            return BuildResponse(
                build=build,
                ai_analysis=ai_analysis,
                similar_builds=similar_builds,
            )

        except Exception as e:
            logger.error(f"Error creating build: {e}")
            raise

    async def get_build(self, build_id: str) -> Optional[Build]:
        """Get build by ID."""
        return self.builds_cache.get(build_id)

    async def list_builds(
        self,
        profession: Optional[Profession] = None,
        game_mode: Optional[GameMode] = None,
        role: Optional[Role] = None,
        limit: int = 20,
    ) -> List[Build]:
        """List builds with filters."""
        builds = list(self.builds_cache.values())

        # Apply filters
        if profession:
            builds = [b for b in builds if b.profession == profession]
        if game_mode:
            builds = [b for b in builds if b.game_mode == game_mode]
        if role:
            builds = [b for b in builds if b.role == role]

        return builds[:limit]

    async def parse_gw2skill_url(self, url: str) -> BuildResponse:
        """Parse a GW2Skill URL."""
        build = await self.parser.parse_url(url)
        if not build:
            raise ValueError("Failed to parse GW2Skill URL")

        ai_analysis = await self._analyze_build(build)
        similar_builds = await self._find_similar_builds(build)

        if not build.id:
            build.id = str(uuid.uuid4())
        self.builds_cache[build.id] = build

        return BuildResponse(
            build=build,
            ai_analysis=ai_analysis,
            similar_builds=similar_builds,
        )

    async def _generate_build_with_ai(self, request: BuildCreate) -> Build:
        """Generate a build using AI."""
        prompt = f"""Generate an optimal {request.profession.value} build for {request.game_mode.value} WvW with {request.role.value} role.

Additional requirements: {request.custom_requirements or 'None'}

Provide a meta-appropriate build with:
- Elite specialization (if applicable)
- Key traits
- Skill recommendations
- Equipment stats
- Playstyle tips"""

        system_prompt = "You are a GW2 WvW build expert. Provide practical, meta-appropriate builds."

        response = await self.ollama.generate(prompt, system_prompt)

        # Create basic build structure
        build = Build(
            id=str(uuid.uuid4()),
            name=f"{request.profession.value} {request.role.value} Build",
            profession=request.profession,
            game_mode=request.game_mode,
            role=request.role,
            description=response,
            source_type="ai",
        )

        return build

    async def _analyze_build(self, build: Build) -> dict[str, str]:
        """Analyze a build with AI."""
        prompt = f"""Analyze this {build.profession.value} build for {build.game_mode.value} WvW:

Role: {build.role.value}
Specialization: {build.specialization or 'Core'}

Provide:
1. Strengths
2. Weaknesses
3. Synergies with other builds
4. Playstyle tips
5. Effectiveness rating (0-10)"""

        response = await self.ollama.generate(prompt, temperature=0.5)

        return {
            "analysis": response,
            "profession": build.profession.value,
            "role": build.role.value,
        }

    async def _find_similar_builds(self, build: Build) -> List[Build]:
        """Find similar builds in cache."""
        similar = []

        for cached_build in self.builds_cache.values():
            if (
                cached_build.id != build.id
                and cached_build.profession == build.profession
                and cached_build.game_mode == build.game_mode
            ):
                similar.append(cached_build)

        return similar[:3]  # Return top 3 similar builds
