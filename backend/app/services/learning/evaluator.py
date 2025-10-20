"""Automatic evaluation service for builds and teams."""

from datetime import datetime
from typing import Dict

from app.core.logging import logger
from app.models.learning import QualityScore, TrainingDatapoint
from app.services.ai.ollama_service import OllamaService


class Evaluator:
    """Evaluates builds and teams for quality scoring."""

    def __init__(self) -> None:
        """Initialize evaluator."""
        self.ollama = OllamaService()

    async def evaluate_datapoint(self, datapoint: TrainingDatapoint) -> QualityScore:
        """
        Evaluate a datapoint and assign quality scores.

        Args:
            datapoint: Datapoint to evaluate

        Returns:
            Quality scores
        """
        try:
            if datapoint.team_id:
                return await self._evaluate_team(datapoint)
            elif datapoint.build_id:
                return await self._evaluate_build(datapoint)
            else:
                raise ValueError("Datapoint must have either build_id or team_id")

        except Exception as e:
            logger.error(f"Error evaluating datapoint {datapoint.id}: {e}")
            # Return default low scores on error
            return QualityScore(
                synergy_score=0.0,
                role_coverage=0.0,
                boon_coverage=0.0,
                meta_compliance=0.0,
                build_validity=0.0,
                overall_score=0.0,
            )

    async def _evaluate_build(self, datapoint: TrainingDatapoint) -> QualityScore:
        """Evaluate a single build."""
        build_data = datapoint.data

        # Prepare evaluation prompt
        prompt = f"""Evaluate this Guild Wars 2 {datapoint.game_mode} build:

Profession: {datapoint.profession}
Role: {datapoint.role}
Source: {datapoint.source.value}

Rate the following aspects from 0-10:
1. Meta Compliance: How well does it match current WvW meta?
2. Build Validity: Are trait/skill selections valid and optimal?
3. Role Effectiveness: How effective for its intended role?
4. Synergy Potential: Potential for team synergies?

Respond with JSON format:
{{
    "meta_compliance": <score>,
    "build_validity": <score>,
    "role_effectiveness": <score>,
    "synergy_potential": <score>,
    "reasoning": "<brief explanation>"
}}"""

        try:
            response = await self.ollama.generate_structured(
                prompt=prompt,
                system_prompt="You are a GW2 WvW expert evaluator. Be strict and accurate.",
            )

            # Map response to QualityScore
            return QualityScore(
                synergy_score=response.get("synergy_potential", 5.0),
                role_coverage=response.get("role_effectiveness", 5.0),
                boon_coverage=5.0,  # Not applicable for single build
                meta_compliance=response.get("meta_compliance", 5.0),
                build_validity=response.get("build_validity", 5.0),
                overall_score=sum(
                    [
                        response.get("meta_compliance", 5.0),
                        response.get("build_validity", 5.0),
                        response.get("role_effectiveness", 5.0),
                        response.get("synergy_potential", 5.0),
                    ]
                )
                / 4.0,
            )

        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            return await self._fallback_evaluation(datapoint)

    async def _evaluate_team(self, datapoint: TrainingDatapoint) -> QualityScore:
        """Evaluate a team composition."""
        team_data = datapoint.data

        prompt = f"""Evaluate this {datapoint.game_mode} WvW team composition:

Team Size: {team_data.get('team_size', 'unknown')}
Description: {team_data.get('description', 'N/A')[:200]}

Rate from 0-10:
1. Synergy Quality: Team synergies and combos
2. Role Coverage: Balance of tanks/dps/support
3. Boon Coverage: Might, fury, protection, etc.
4. Meta Compliance: Alignment with current WvW meta
5. Overall Effectiveness: Overall team strength

Respond with JSON:
{{
    "synergy_score": <score>,
    "role_coverage": <score>,
    "boon_coverage": <score>,
    "meta_compliance": <score>,
    "overall_effectiveness": <score>,
    "reasoning": "<explanation>"
}}"""

        try:
            response = await self.ollama.generate_structured(
                prompt=prompt,
                system_prompt="You are a GW2 WvW team composition expert. Evaluate critically.",
            )

            return QualityScore(
                synergy_score=response.get("synergy_score", 5.0),
                role_coverage=response.get("role_coverage", 5.0),
                boon_coverage=response.get("boon_coverage", 5.0),
                meta_compliance=response.get("meta_compliance", 5.0),
                build_validity=8.0,  # Teams are always valid if they exist
                overall_score=response.get("overall_effectiveness", 5.0),
            )

        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            return await self._fallback_evaluation(datapoint)

    async def _fallback_evaluation(self, datapoint: TrainingDatapoint) -> QualityScore:
        """Fallback evaluation when AI fails."""
        # Simple heuristic-based evaluation
        base_score = 5.0

        # Bonus for certain sources
        if datapoint.source == "community_scrape":
            base_score += 1.0
        elif datapoint.source == "ai_generated":
            base_score += 0.5

        return QualityScore(
            synergy_score=base_score,
            role_coverage=base_score,
            boon_coverage=base_score,
            meta_compliance=base_score,
            build_validity=base_score,
            overall_score=base_score,
        )

    async def mark_validated(self, datapoint: TrainingDatapoint) -> None:
        """Mark a datapoint as validated."""
        datapoint.is_validated = True
        datapoint.validation_date = datetime.utcnow()
