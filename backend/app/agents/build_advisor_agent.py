from dataclasses import dataclass
from typing import Any, Dict, List

from app.core.logging import logger
from app.services.ai.ollama_service import OllamaService
from app.services.learning.data_collector import DataCollector
from app.models.learning import DataSource


@dataclass
class BuildCandidate:
    """Candidat de build issu du moteur d'optimisation.

    Cette structure est volontairement simple et découplée du moteur
    (OptimizationResult) pour permettre une future intégration LLM.
    """

    id: str
    prefix: str
    role: str
    rune: str
    sigils: List[str]
    total_damage: float
    survivability: float
    overall_score: float
    relic: str | None = None


@dataclass
class AdvisorChoice:
    candidate: BuildCandidate
    reason: str
    ranked_candidates: list[BuildCandidate] | None = None


class BuildAdvisorAgent:
    """Sous-agent chargé de choisir le meilleur build parmi plusieurs candidats.

    V1: logique purement heuristique, pensée pour le WvW zerg (débutants).
    V2: pourra déléguer au LLM en lui envoyant la liste des candidats et
    le contexte (niveau du joueur, mode de jeu, préférences).
    """

    def __init__(self) -> None:
        self.ollama = OllamaService()
        # Data collector for logging advisor decisions as training data
        self.collector = DataCollector()

    def _normalize_role(self, role: str) -> str:
        r = role.lower()
        if r in {"heal", "healer"}:
            return "heal"
        if r in {"boon", "boons"}:
            return "boon"
        if r in {"tank", "stab"}:
            return "tank"
        if r in {"support", "cleanse"}:
            return "support"
        return "dps"

    async def choose_best_candidate(
        self,
        candidates: List[BuildCandidate],
        role: str,
        context: Dict[str, Any] | None = None,
    ) -> AdvisorChoice:
        ctx = context or {}

        if not candidates:
            raise ValueError("No candidates provided to BuildAdvisorAgent")

        # Tenter d'abord la voie LLM pour laisser l'IA arbitrer les presets.
        try:
            llm_choice = await self._choose_with_llm(candidates, role, ctx)
            if llm_choice is not None:
                return llm_choice
        except Exception as e:  # pragma: no cover - fallback robuste
            logger.warning(
                "BuildAdvisorAgent LLM choice failed; falling back to heuristic.",
                extra={"error": str(e)},
            )

        # Fallback: logique heuristique historique
        return self._choose_best_candidate_heuristic(candidates, role, ctx)

    def _choose_best_candidate_heuristic(
        self,
        candidates: List[BuildCandidate],
        role: str,
        context: Dict[str, Any],
    ) -> AdvisorChoice:
        if not candidates:
            raise ValueError("No candidates provided to BuildAdvisorAgent")

        experience = str(context.get("experience", "beginner")).lower()
        mode = str(context.get("mode", "wvw_zerg")).lower()

        role_cat = self._normalize_role(role)

        if len(candidates) == 1:
            single = candidates[0]
            reason_single = (
                f"Un seul preset disponible pour le rôle {role_cat}: "
                f"{single.prefix} (niveau {experience})."
            )
            return AdvisorChoice(candidate=single, reason=reason_single, ranked_candidates=[single])

        if role_cat == "dps":
            if experience == "expert":
                primary_w, surv_w = 0.9, 0.1
            elif experience == "intermediate":
                primary_w, surv_w = 0.7, 0.3
            else:
                primary_w, surv_w = 0.6, 0.4
        elif role_cat == "tank":
            primary_w, surv_w = 0.2, 0.8
        elif role_cat in {"heal", "boon", "support"}:
            if experience == "expert":
                primary_w, surv_w = 0.8, 0.2
            elif experience == "intermediate":
                primary_w, surv_w = 0.5, 0.5
            else:
                primary_w, surv_w = 0.4, 0.6
        else:
            if experience == "expert":
                primary_w, surv_w = 0.8, 0.2
            elif experience == "intermediate":
                primary_w, surv_w = 0.7, 0.3
            else:
                primary_w, surv_w = 0.6, 0.4

        mode_cat = "zerg"
        if "outnumber" in mode:
            mode_cat = "outnumber"
        elif "roam" in mode:
            mode_cat = "roam"

        if mode_cat == "outnumber":
            primary_w *= 0.85
            surv_w *= 1.15
        elif mode_cat == "roam":
            primary_w *= 1.1
            surv_w *= 0.9

        total_w = primary_w + surv_w
        if total_w > 0:
            primary_w /= total_w
            surv_w /= total_w

        if role_cat == "dps":
            primary_values = [c.total_damage for c in candidates]
        else:
            primary_values = [c.overall_score for c in candidates]
        surv_values = [c.survivability for c in candidates]

        max_primary = max(primary_values) if primary_values else 0.0
        max_surv = max(surv_values) if surv_values else 0.0

        def score_candidate(c: BuildCandidate) -> float:
            if role_cat == "dps":
                primary = c.total_damage
            else:
                primary = c.overall_score

            primary_norm = primary / max_primary if max_primary > 0 else 0.0
            surv_norm = c.survivability / max_surv if max_surv > 0 else 0.0

            return primary_norm * primary_w + surv_norm * surv_w

        ranked = sorted(candidates, key=score_candidate, reverse=True)
        best = ranked[0]

        primary_label = "dégâts" if role_cat == "dps" else "performance globale"
        reason = (
            f"Choix du preset {best.prefix} pour le rôle {role_cat} "
            f"avec priorité {int(primary_w * 100)}% sur les {primary_label} "
            f"et {int(surv_w * 100)}% sur la survie (niveau {experience})."
        )

        return AdvisorChoice(candidate=best, reason=reason, ranked_candidates=ranked)

    async def _choose_with_llm(
        self,
        candidates: List[BuildCandidate],
        role: str,
        context: Dict[str, Any],
    ) -> AdvisorChoice | None:
        if not candidates:
            return None

        role_cat = self._normalize_role(role)
        experience = str(context.get("experience", "beginner")).lower()
        mode = str(context.get("mode", "wvw_zerg")).lower()

        # Limiter le nombre d'options envoyées au LLM pour le coût et la clarté.
        # On prend les meilleures options selon le score global du moteur.
        MAX_OPTIONS = 5
        sorted_candidates = sorted(candidates, key=lambda c: c.overall_score, reverse=True)
        limited_candidates = sorted_candidates[:MAX_OPTIONS]

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "best_id": {"type": "string"},
                "reason": {"type": "string"},
                "ranking": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["best_id", "reason"],
        }

        options_lines: List[str] = []
        for c in limited_candidates:
            sigils_str = ", ".join(c.sigils)
            options_lines.append(
                f"- id: {c.id} | prefix: {c.prefix} | rune: {c.rune} | sigils: [{sigils_str}] | "
                f"total_damage: {c.total_damage:.1f} | survivability: {c.survivability:.3f} | "
                f"overall_score: {c.overall_score:.3f}"
            )

        options_block = "\n".join(options_lines)

        prompt = (
            "Tu es un conseiller de builds Guild Wars 2 expert en WvW.\n"
            "Contexte :\n"
            f"- Rôle logique : {role_cat}\n"
            f"- Mode : {mode}\n"
            f"- Niveau de l'équipe : {experience}\n\n"
            "On te donne plusieurs options de gear déjà évaluées par un moteur mathématique.\n"
            "Chaque option fournit un préfixe de stats, une rune, des sigils, et des scores de dégâts "
            "et de survie. Utilise ta connaissance de la méta WvW pour choisir l'option la plus "
            "réaliste et jouable pour ce contexte (par exemple éviter les healers en carton en roam, "
            "valoriser les bonnes runes/meta, etc.).\n\n"
            "Options :\n"
            f"{options_block}\n\n"
            "Donne ta réponse STRICTEMENT au format JSON en suivant le schéma: {best_id: string, "
            "reason: string, ranking: string[]}.")

        system_prompt = (
            "Tu es un arbitre de builds WvW pour Guild Wars 2. "
            "Réponds toujours en JSON valide uniquement, en français."
        )

        result = await self.ollama.generate_structured(
            prompt=prompt,
            system_prompt=system_prompt,
            schema=schema,
            max_tokens=512,
        )

        best_id = str(result.get("best_id", "")).strip()
        reason = str(result.get("reason", "")).strip()
        ranking_ids = result.get("ranking") or []

        candidates_by_id: Dict[str, BuildCandidate] = {c.id: c for c in limited_candidates}
        best = candidates_by_id.get(best_id)
        if best is None:
            logger.warning(
                "BuildAdvisorAgent LLM returned unknown best_id; falling back to heuristic.",
                extra={"best_id": best_id},
            )
            return None

        ranked: List[BuildCandidate] = []
        for cid in ranking_ids:
            cid_str = str(cid)
            cand = candidates_by_id.get(cid_str)
            if cand is not None and cand not in ranked:
                ranked.append(cand)

        for c in limited_candidates:
            if c not in ranked:
                ranked.append(c)

        if not reason:
            reason = f"Choix du preset {best.prefix} via arbitre LLM pour le rôle {role_cat}."

        # Enregistrer cette décision comme datapoint d'entraînement compact.
        try:
            decision_payload: Dict[str, Any] = {
                "kind": "advisor_decision",
                "mode": mode,
                "role_cat": role_cat,
                "experience": experience,
                "candidates": [
                    {
                        "id": c.id,
                        "prefix": c.prefix,
                        "rune": c.rune,
                        "sigils": list(c.sigils),
                        "total_damage": c.total_damage,
                        "survivability": c.survivability,
                        "overall_score": c.overall_score,
                        "relic": c.relic,
                    }
                    for c in limited_candidates
                ],
                "best_id": best_id,
                "reason": reason,
            }

            await self.collector.collect_advisor_decision(
                decision=decision_payload,
                game_mode=mode,
                profession=None,
                role=role_cat,
                source=DataSource.AI_GENERATED,
            )
        except Exception as e:  # pragma: no cover - la collecte ne doit jamais casser la décision
            logger.warning(
                "Failed to collect advisor decision datapoint",
                extra={"error": str(e)},
            )

        return AdvisorChoice(candidate=best, reason=reason, ranked_candidates=ranked)
