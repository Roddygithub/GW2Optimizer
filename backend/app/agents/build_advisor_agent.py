from dataclasses import dataclass
from typing import Any, Dict, List


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

    def choose_best_candidate(
        self,
        candidates: List[BuildCandidate],
        role: str,
        context: Dict[str, Any] | None = None,
    ) -> AdvisorChoice:
        if not candidates:
            raise ValueError("No candidates provided to BuildAdvisorAgent")
        
        ctx = context or {}
        experience = str(ctx.get("experience", "beginner")).lower()
        mode = str(ctx.get("mode", "wvw_zerg")).lower()

        role_cat = self._normalize_role(role)

        if len(candidates) == 1:
            single = candidates[0]
            reason_single = (
                f"Un seul preset disponible pour le rôle {role_cat}: "
                f"{single.prefix} (niveau {experience})."
            )
            return AdvisorChoice(candidate=single, reason=reason_single, ranked_candidates=[single])

        # Poids par défaut pour un contexte WvW zerg, ajustés par niveau
        if role_cat == "dps":
            if experience == "expert":
                primary_w, surv_w = 0.9, 0.1
            elif experience == "intermediate":
                primary_w, surv_w = 0.7, 0.3
            else:  # beginner / défaut
                primary_w, surv_w = 0.6, 0.4
        elif role_cat == "tank":
            # Un tank reste avant tout tank, quel que soit le niveau
            primary_w, surv_w = 0.2, 0.8
        elif role_cat in {"heal", "boon", "support"}:
            # Supports: plus de survie pour les débutants, plus de
            # performance pour les joueurs expérimentés.
            if experience == "expert":
                primary_w, surv_w = 0.8, 0.2
            elif experience == "intermediate":
                primary_w, surv_w = 0.5, 0.5
            else:  # beginner
                primary_w, surv_w = 0.4, 0.6
        else:
            # Rôle générique/hybride
            if experience == "expert":
                primary_w, surv_w = 0.8, 0.2
            elif experience == "intermediate":
                primary_w, surv_w = 0.7, 0.3
            else:
                primary_w, surv_w = 0.6, 0.4

        # Ajuster légèrement selon le mode de jeu (zerg/outnumber/roam)
        mode_cat = "zerg"
        if "outnumber" in mode:
            mode_cat = "outnumber"
        elif "roam" in mode:
            mode_cat = "roam"

        if mode_cat == "outnumber":
            # En infériorité numérique, on valorise un peu plus la survie
            primary_w *= 0.85
            surv_w *= 1.15
        elif mode_cat == "roam":
            # En roaming, on peut se permettre un peu plus de greed
            primary_w *= 1.1
            surv_w *= 0.9

        # Normaliser pour garder une somme de 1
        total_w = primary_w + surv_w
        if total_w > 0:
            primary_w /= total_w
            surv_w /= total_w

        # Valeurs de référence pour la normalisation
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

        # Classer tous les candidats selon ce score heuristique
        ranked = sorted(candidates, key=score_candidate, reverse=True)
        best = ranked[0]

        primary_label = "dégâts" if role_cat == "dps" else "performance globale"
        reason = (
            f"Choix du preset {best.prefix} pour le rôle {role_cat} "
            f"avec priorité {int(primary_w * 100)}% sur les {primary_label} "
            f"et {int(surv_w * 100)}% sur la survie (niveau {experience})."
        )

        return AdvisorChoice(candidate=best, reason=reason, ranked_candidates=ranked)
