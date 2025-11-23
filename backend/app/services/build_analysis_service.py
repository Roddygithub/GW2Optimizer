from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.services.gw2_api_client import GW2APIClient
from app.agents.analyst_agent import AnalystAgent


class BuildAnalysisService:
    """Service d'analyse de synergie de build GW2.

    Agrège les données GW2 (spécialisation, traits, skills) puis délègue
    l'analyse de synergie à l'AnalystAgent.
    """

    def __init__(
        self,
        gw2_client: Optional[GW2APIClient] = None,
        analyst_agent: Optional[AnalystAgent] = None,
    ) -> None:
        self.gw2_client = gw2_client or GW2APIClient()
        self.analyst_agent = analyst_agent or AnalystAgent()

    def _minify_facts(self, facts: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """Réduit un tableau de facts GW2 aux champs utiles pour l'analyse.

        Ne conserve que: text, type, percent, value, target. Supprime notamment les icônes.
        """
        if not facts:
            return None

        simplified: List[Dict[str, Any]] = []
        for f in facts:
            if not isinstance(f, dict):
                continue
            fact_view: Dict[str, Any] = {}
            for key in ("text", "type", "percent", "value", "target"):
                if key in f:
                    fact_view[key] = f[key]
            if fact_view:
                simplified.append(fact_view)

        return simplified or None

    def _minify_gw2_object(self, obj: Dict[str, Any], extra_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Conserve uniquement les champs sémantiques utiles pour l'analyse.

        - Garde systématiquement: id, name, description (quand présents)
        - Ajoute certains champs contextuels via extra_fields (ex: slot, type, profession, elite)
        - Minifie les tableaux de facts / traited_facts
        """
        view: Dict[str, Any] = {}

        for key in ("id", "name", "description"):
            if key in obj:
                view[key] = obj[key]

        if extra_fields:
            for key in extra_fields:
                if key in obj:
                    view[key] = obj[key]

        if "facts" in obj:
            min_facts = self._minify_facts(obj.get("facts"))
            if min_facts is not None:
                view["facts"] = min_facts

        if "traited_facts" in obj:
            min_traited = self._minify_facts(obj.get("traited_facts"))
            if min_traited is not None:
                view["traited_facts"] = min_traited

        return view

    async def analyze_build_synergy(
        self,
        specialization_id: Optional[int],
        trait_ids: List[int],
        skill_ids: List[int],
        context: str = "WvW Zerg",
    ) -> Dict[str, Any]:
        """Analyse la synergie d'un build GW2.

        Args:
            specialization_id: ID de la spécialisation principale (ex: Firebrand)
            trait_ids: Liste d'IDs de traits sélectionnés
            skill_ids: Liste d'IDs de skills inclus dans le build
            context: Contexte d'analyse (WvW, PvE, Roaming, etc.)
        """

        logger.info(
            "Analyzing build synergy",
            extra={
                "specialization_id": specialization_id,
                "trait_ids": trait_ids,
                "skill_ids": skill_ids,
                "context": context,
            },
        )

        # ==================== Fetch GW2 data ====================
        spec_data: Optional[Dict[str, Any]] = None
        traits_data: List[Dict[str, Any]] = []
        skills_data: List[Dict[str, Any]] = []

        # Spécialisation
        if specialization_id:
            spec_data = await self.gw2_client.get_specialization_details(specialization_id)

        # Traits (un par un pour gestion de 404 individuelle)
        for tid in trait_ids:
            trait = await self.gw2_client.get_trait_details(tid)
            if trait:
                traits_data.append(trait)

        # Skills (utiliser l'endpoint de liste pour limiter les requêtes)
        if skill_ids:
            try:
                skills_data = await self.gw2_client.get_skills(skill_ids)
            except Exception as e:
                logger.error(f"Failed to fetch skills for build analysis: {e}")
                skills_data = []

        # ==================== Basic consistency validation ====================
        if specialization_id and not spec_data:
            raise ValueError(f"Specialization {specialization_id} not found in GW2 API")

        spec_profession: Optional[str] = None
        if spec_data:
            raw_prof = spec_data.get("profession")
            if isinstance(raw_prof, str) and raw_prof:
                spec_profession = raw_prof

        # Validation stricte uniquement sur les skills pour l'instant.
        # Les traits peuvent appartenir à des spécialisations "core" de la même
        # profession (ex: Honor + Valor + Firebrand pour Guardian), ce qui
        # rend une validation naïve sur le champ "specialization" trop stricte.
        invalid_skills: List[int] = []

        # Si on a une spécialisation et une profession associée, vérifier la cohérence des skills.
        if specialization_id and spec_profession:
            for s in skills_data:
                professions = s.get("professions")
                if isinstance(professions, list) and professions:
                    if spec_profession not in professions:
                        skill_id = s.get("id")
                        if isinstance(skill_id, int):
                            invalid_skills.append(skill_id)

        if invalid_skills:
            logger.warning(
                "Inconsistent build data for analysis (skills)",
                extra={
                    "specialization_id": specialization_id,
                    "spec_profession": spec_profession,
                    "invalid_skills": invalid_skills,
                },
            )
            raise ValueError(
                "Inconsistent build: some skill IDs do not match the selected specialization/profession. "
                f"Invalid skills: {invalid_skills}."
            )

        # ==================== Aggregate for AI ====================
        spec_view: Optional[Dict[str, Any]] = None
        if spec_data:
            # Conserver les informations essentielles de la spécialisation
            spec_view = self._minify_gw2_object(spec_data, extra_fields=["profession", "elite"])

        traits_view: List[Dict[str, Any]] = []
        for t in traits_data:
            # Garder surtout: id, name, description, slot (+ facts éventuels)
            traits_view.append(self._minify_gw2_object(t, extra_fields=["slot"]))

        skills_view: List[Dict[str, Any]] = []
        for s in skills_data:
            # Garder: id, name, description, type, slot, flags, facts/traited_facts minifiés
            skills_view.append(self._minify_gw2_object(s, extra_fields=["type", "slot", "flags"]))

        build_payload: Dict[str, Any] = {
            "context": context,
            "specialization": spec_view,
            "traits": traits_view,
            "skills": skills_view,
        }

        # ==================== Delegate to AnalystAgent ====================
        envelope = await self.analyst_agent.execute({"build_data": build_payload, "context": context})
        if not envelope.get("success"):
            error = envelope.get("error") or "unknown_error"
            raise RuntimeError(f"AnalystAgent build analysis failed: {error}")

        return envelope["result"]
