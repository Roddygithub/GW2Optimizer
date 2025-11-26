"""
Meta Adaptative Agent

Agent IA spécialisé dans l'analyse et l'adaptation automatique aux métas GW2.
Analyse les tendances, détecte les changements de méta, et propose des adaptations.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.db.base import SessionLocal
from app.models import SavedBuildDB


class MetaAgent(BaseAgent):
    """
    Agent d'analyse et d'adaptation de méta.

    Capacités:
    - Analyse des tendances de builds populaires
    - Détection des changements de méta
    - Recommandations d'adaptation
    - Scoring de viabilité des builds
    - Prédiction des évolutions de méta

    Example:
        ```python
        agent = MetaAgent()
        result = await agent.run({
            "game_mode": "zerg",
            "profession": "Guardian",
            "current_meta": {...},
            "historical_data": [...]
        })
        ```
    """

    def __init__(self):
        """Initialise le Meta Agent."""
        super().__init__(
            name="MetaAgent",
            description="Agent d'analyse et d'adaptation de méta GW2",
            version="1.0.0",
            capabilities=[
                "meta_analysis",
                "trend_detection",
                "build_viability_scoring",
                "adaptation_recommendations",
                "meta_prediction",
            ],
        )
        self.meta_history: List[Dict[str, Any]] = []
        self.trend_threshold = 0.15  # 15% de changement pour détecter une tendance

    async def _initialize_impl(self) -> None:
        """Initialisation spécifique du Meta Agent."""
        logger.info("Initializing Meta Agent with historical data...")
        # Charger l'historique des métas si disponible
        await self._load_meta_history()

    async def _load_meta_history(self) -> None:
        """Charge l'historique des métas depuis le stockage."""
        self.meta_history = []

        try:
            async with SessionLocal() as session:  # type: AsyncSession
                stmt = (
                    select(
                        SavedBuildDB.game_mode,
                        func.date(SavedBuildDB.created_at).label("day"),
                        func.count().label("count"),
                    )
                    .group_by("day", SavedBuildDB.game_mode)
                    .order_by("day")
                )
                result = await session.execute(stmt)
                rows = result.all()

            for row in rows:
                day_value = row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day)
                self.meta_history.append(
                    {
                        "game_mode": row.game_mode,
                        "day": day_value,
                        "count": int(row.count),
                    }
                )

            logger.info(
                "Meta history loaded successfully",
                extra={"entries": len(self.meta_history)},
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to load meta history: {exc}")
            self.meta_history = []

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'analyse de méta.

        Args:
            inputs: Dictionnaire contenant:
                - game_mode (str): Mode de jeu (zerg, raid_guild, roaming)
                - profession (str, optional): Profession à analyser
                - current_builds (List[Dict], optional): Builds actuels à analyser
                - time_range (int, optional): Période d'analyse en jours (défaut: 30)

        Returns:
            Dictionnaire contenant:
                - meta_snapshot: État actuel du méta
                - trends: Tendances détectées
                - recommendations: Recommandations d'adaptation
                - viability_scores: Scores de viabilité
                - predictions: Prédictions d'évolution
        """
        game_mode = inputs.get("game_mode")
        profession = inputs.get("profession")
        current_builds = inputs.get("current_builds", [])
        time_range = inputs.get("time_range", 30)

        logger.info(
            f"Analyzing meta for game_mode={game_mode}, " f"profession={profession}, time_range={time_range} days"
        )

        # Analyse du méta actuel
        meta_snapshot = await self._analyze_current_meta(game_mode, profession)

        # Détection des tendances
        trends = await self._detect_trends(game_mode, profession, time_range)

        # Calcul des scores de viabilité
        viability_scores = await self._calculate_viability_scores(current_builds, meta_snapshot)

        # Génération des recommandations
        recommendations = await self._generate_recommendations(meta_snapshot, trends, viability_scores)

        # Prédictions d'évolution
        predictions = await self._predict_meta_evolution(trends, time_range)

        return {
            "meta_snapshot": meta_snapshot,
            "trends": trends,
            "recommendations": recommendations,
            "viability_scores": viability_scores,
            "predictions": predictions,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    async def _analyze_current_meta(self, game_mode: str, profession: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyse l'état actuel du méta.

        Args:
            game_mode: Mode de jeu
            profession: Profession (optionnel)

        Returns:
            Snapshot du méta actuel
        """
        logger.info(f"Analyzing current meta for {game_mode}")

        meta_data = {
            "game_mode": game_mode,
            "profession": profession,
            "top_builds": await self._get_top_builds(game_mode, profession),
            "popular_roles": await self._get_popular_roles(game_mode),
            "common_synergies": await self._get_common_synergies(game_mode),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return meta_data

    async def _get_top_builds(
        self, game_mode: str, profession: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Récupère les builds les plus populaires."""
        builds: List[Dict[str, Any]] = []

        try:
            async with SessionLocal() as session:  # type: AsyncSession
                stmt = select(SavedBuildDB).where(SavedBuildDB.game_mode == game_mode)

                if profession:
                    stmt = stmt.where(SavedBuildDB.profession == profession)

                # Utiliser la date de création comme proxy de "popularité récente"
                stmt = stmt.order_by(SavedBuildDB.created_at.desc()).limit(limit)

                result = await session.execute(stmt)
                rows = list(result.scalars().all())

            for row in rows:
                builds.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "profession": row.profession,
                        "specialization": row.specialization,
                        "game_mode": row.game_mode,
                        "synergy_score": row.synergy_score,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "source_url": row.source_url,
                    }
                )

            return builds
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error(f"Failed to load top builds: {exc}")
            return []

    async def _get_popular_roles(self, game_mode: str) -> List[Dict[str, Any]]:
        """Récupère les rôles les plus populaires."""
        # Rôles typiques par mode de jeu
        role_distribution = {
            "zerg": [
                {"role": "support", "popularity": 0.35},
                {"role": "dps", "popularity": 0.40},
                {"role": "tank", "popularity": 0.15},
                {"role": "healer", "popularity": 0.10},
            ],
            "raid_guild": [
                {"role": "support", "popularity": 0.30},
                {"role": "dps", "popularity": 0.45},
                {"role": "tank", "popularity": 0.15},
                {"role": "healer", "popularity": 0.10},
            ],
            "roaming": [
                {"role": "dps", "popularity": 0.60},
                {"role": "support", "popularity": 0.25},
                {"role": "tank", "popularity": 0.15},
            ],
        }

        return role_distribution.get(game_mode, [])

    async def _get_common_synergies(self, game_mode: str) -> List[Dict[str, Any]]:
        """Récupère les synergies communes."""
        synergies: List[Dict[str, Any]] = []

        try:
            async with SessionLocal() as session:  # type: AsyncSession
                stmt = (
                    select(
                        SavedBuildDB.profession,
                        SavedBuildDB.specialization,
                        SavedBuildDB.synergy_score,
                        func.count().label("count"),
                    )
                    .where(SavedBuildDB.game_mode == game_mode)
                    .group_by(
                        SavedBuildDB.profession,
                        SavedBuildDB.specialization,
                        SavedBuildDB.synergy_score,
                    )
                    .order_by(func.count().desc())
                    .limit(20)
                )

                result = await session.execute(stmt)
                rows = result.all()

            total = sum(int(row.count) for row in rows) or 1

            for row in rows:
                count = int(row.count)
                synergies.append(
                    {
                        "profession": row.profession,
                        "specialization": row.specialization,
                        "synergy_score": row.synergy_score,
                        "occurrences": count,
                        "frequency": round(count / total, 4),
                    }
                )

            return synergies
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error(f"Failed to compute common synergies: {exc}")
            return []

    async def _detect_trends(self, game_mode: str, profession: Optional[str], time_range: int) -> List[Dict[str, Any]]:
        """
        Détecte les tendances dans le méta.

        Args:
            game_mode: Mode de jeu
            profession: Profession (optionnel)
            time_range: Période d'analyse en jours

        Returns:
            Liste des tendances détectées
        """
        logger.info(f"Detecting trends over {time_range} days for game_mode={game_mode}, profession={profession}")

        now = datetime.utcnow()
        recent_start = now - timedelta(days=time_range)
        previous_start = now - timedelta(days=2 * time_range)

        try:
            async with SessionLocal() as session:  # type: AsyncSession
                # Fenêtre récente
                recent_stmt = select(
                    SavedBuildDB.specialization,
                    func.count().label("count"),
                ).where(
                    SavedBuildDB.game_mode == game_mode,
                    SavedBuildDB.created_at >= recent_start,
                )

                if profession:
                    recent_stmt = recent_stmt.where(SavedBuildDB.profession == profession)

                recent_stmt = recent_stmt.group_by(SavedBuildDB.specialization)
                recent_rows = (await session.execute(recent_stmt)).all()

                # Fenêtre précédente
                previous_stmt = select(
                    SavedBuildDB.specialization,
                    func.count().label("count"),
                ).where(
                    SavedBuildDB.game_mode == game_mode,
                    SavedBuildDB.created_at >= previous_start,
                    SavedBuildDB.created_at < recent_start,
                )

                if profession:
                    previous_stmt = previous_stmt.where(SavedBuildDB.profession == profession)

                previous_stmt = previous_stmt.group_by(SavedBuildDB.specialization)
                previous_rows = (await session.execute(previous_stmt)).all()

            recent_counts = {row.specialization or "Unknown": int(row.count) for row in recent_rows}
            previous_counts = {row.specialization or "Unknown": int(row.count) for row in previous_rows}

            recent_total = sum(recent_counts.values())
            previous_total = sum(previous_counts.values()) or 1

            trends: List[Dict[str, Any]] = []

            if recent_total == 0:
                # Pas de données récentes → aucune tendance fiable
                return trends

            for spec, recent_count in recent_counts.items():
                prev_count = previous_counts.get(spec, 0)

                recent_share = recent_count / recent_total
                previous_share = prev_count / previous_total
                change = recent_share - previous_share

                if change <= 0 or change < self.trend_threshold:
                    continue

                trends.append(
                    {
                        "type": "specialization_trend",
                        "specialization": spec,
                        "description": f"Augmentation de la popularité de {spec}",
                        "change_percentage": round(change, 4),
                        "confidence": 0.8,
                        "detected_at": datetime.utcnow().isoformat(),
                    }
                )

            return trends
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error(f"Failed to detect trends: {exc}")
            return []

    async def _calculate_viability_scores(
        self, builds: List[Dict[str, Any]], meta_snapshot: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calcule les scores de viabilité des builds.

        Args:
            builds: Liste des builds à évaluer
            meta_snapshot: État actuel du méta

        Returns:
            Dictionnaire {build_id: score}
        """
        logger.info(f"Calculating viability scores for {len(builds)} builds")

        scores = {}

        for build in builds:
            build_id = build.get("id", "unknown")

            # Facteurs de viabilité
            role_score = await self._score_role_viability(build.get("role"), meta_snapshot)

            profession_score = await self._score_profession_viability(build.get("profession"), meta_snapshot)

            synergy_score = await self._score_synergy_potential(build, meta_snapshot)

            # Score global (moyenne pondérée)
            total_score = role_score * 0.35 + profession_score * 0.30 + synergy_score * 0.35

            scores[build_id] = round(total_score, 2)

        return scores

    async def _score_role_viability(self, role: str, meta_snapshot: Dict[str, Any]) -> float:
        """Score la viabilité d'un rôle dans le méta actuel."""
        popular_roles = meta_snapshot.get("popular_roles", [])

        for role_data in popular_roles:
            if role_data.get("role") == role:
                return role_data.get("popularity", 0.5)

        return 0.5  # Score neutre par défaut

    async def _score_profession_viability(self, profession: str, meta_snapshot: Dict[str, Any]) -> float:
        """Score la viabilité d'une profession dans le méta actuel."""
        game_mode = meta_snapshot.get("game_mode")

        if not profession or not game_mode:
            return 0.7  # Score par défaut

        try:
            async with SessionLocal() as session:  # type: AsyncSession
                total_stmt = select(func.count()).where(SavedBuildDB.game_mode == game_mode)
                total_builds = await session.scalar(total_stmt) or 0

                if total_builds == 0:
                    return 0.7

                prof_stmt = select(func.count()).where(
                    SavedBuildDB.game_mode == game_mode,
                    SavedBuildDB.profession == profession,
                )
                prof_builds = await session.scalar(prof_stmt) or 0

            popularity = prof_builds / total_builds

            # Mapper la popularité [0, 1] vers un score [0.4, 0.95]
            score = 0.4 + 0.55 * min(popularity, 1.0)
            return round(score, 2)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error(f"Failed to score profession viability: {exc}")
            return 0.7

    async def _score_synergy_potential(self, build: Dict[str, Any], meta_snapshot: Dict[str, Any]) -> float:
        """Score le potentiel de synergie d'un build."""
        specialization = build.get("specialization")
        common_synergies: List[Dict[str, Any]] = meta_snapshot.get("common_synergies", [])

        if not specialization or not common_synergies:
            return 0.6

        try:
            total_occurrences = sum(int(item.get("occurrences", 0)) for item in common_synergies) or 1

            for item in common_synergies:
                if item.get("specialization") != specialization:
                    continue

                occ = int(item.get("occurrences", 0))
                freq = occ / total_occurrences

                # Mapper la fréquence vers un score [0.5, 0.95]
                score = 0.5 + 0.45 * min(freq * 2, 1.0)
                return round(score, 2)

            return 0.6
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error(f"Failed to score synergy potential: {exc}")
            return 0.6

    async def _generate_recommendations(
        self, meta_snapshot: Dict[str, Any], trends: List[Dict[str, Any]], viability_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Génère des recommandations d'adaptation.

        Args:
            meta_snapshot: État actuel du méta
            trends: Tendances détectées
            viability_scores: Scores de viabilité

        Returns:
            Liste de recommandations
        """
        logger.info("Generating adaptation recommendations")

        recommendations = []

        # Recommandations basées sur les tendances
        for trend in trends:
            if trend.get("change_percentage", 0) > self.trend_threshold:
                recommendations.append(
                    {
                        "type": "trend_adaptation",
                        "priority": "high" if trend.get("confidence", 0) > 0.8 else "medium",
                        "description": f"Adapter aux tendances: {trend.get('description')}",
                        "suggested_actions": ["Considérer les builds support", "Renforcer les synergies d'équipe"],
                        "confidence": trend.get("confidence", 0.5),
                    }
                )

        # Recommandations basées sur les scores de viabilité
        low_viability_builds = [build_id for build_id, score in viability_scores.items() if score < 0.5]

        if low_viability_builds:
            recommendations.append(
                {
                    "type": "viability_improvement",
                    "priority": "medium",
                    "description": f"{len(low_viability_builds)} builds avec faible viabilité détectés",
                    "suggested_actions": [
                        "Revoir les rôles des builds",
                        "Optimiser les synergies",
                        "Mettre à jour l'équipement",
                    ],
                    "affected_builds": low_viability_builds,
                }
            )

        return recommendations

    async def _predict_meta_evolution(self, trends: List[Dict[str, Any]], time_range: int) -> Dict[str, Any]:
        """
        Prédit l'évolution du méta.

        Args:
            trends: Tendances détectées
            time_range: Période d'analyse

        Returns:
            Prédictions d'évolution
        """
        logger.info("Predicting meta evolution")

        # Analyse des tendances pour prédiction
        strong_trends = [t for t in trends if t.get("confidence", 0) > 0.7]

        prediction = {"timeframe": f"{time_range} days", "confidence": 0.65, "expected_changes": [], "risk_factors": []}

        if strong_trends:
            prediction["expected_changes"].append(
                {"type": "role_shift", "description": "Augmentation probable des builds support", "probability": 0.75}
            )

        prediction["risk_factors"].append(
            {
                "type": "game_balance_patch",
                "description": "Patch d'équilibrage pourrait modifier le méta",
                "impact": "high",
            }
        )

        return prediction

    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Valide les entrées du Meta Agent."""
        await super().validate_inputs(inputs)

        if "game_mode" not in inputs:
            raise ValueError("game_mode is required")

        valid_modes = ["zerg", "raid_guild", "roaming"]
        if inputs["game_mode"] not in valid_modes:
            raise ValueError(f"Invalid game_mode. Must be one of: {', '.join(valid_modes)}")

        if "time_range" in inputs:
            time_range = inputs["time_range"]
            if not isinstance(time_range, int) or time_range < 1 or time_range > 365:
                raise ValueError("time_range must be between 1 and 365 days")

    async def _cleanup_impl(self) -> None:
        """Nettoyage spécifique du Meta Agent."""
        logger.info("Cleaning up Meta Agent resources")
        self.meta_history.clear()
