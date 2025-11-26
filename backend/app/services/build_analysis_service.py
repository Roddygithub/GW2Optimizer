from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.services.gw2_api_client import GW2APIClient
from app.agents.analyst_agent import AnalystAgent
from app.engine.damage import ARMOR_HEAVY, WEAPON_STRENGTH_AVG, calculate_damage
from app.agents.build_equipment_optimizer import get_build_optimizer, OptimizationResult
from app.engine.gear.prefixes import get_prefix_stats
from app.agents.build_advisor_agent import BuildAdvisorAgent, BuildCandidate, AdvisorChoice
from app.services.gear_prefix_validator import filter_prefix_names_by_itemstats


class BuildAnalysisService:
    """Service d'analyse de synergie de build GW2.

    Agrège les données GW2 (spécialisation, traits, skills) puis délègue
    l'analyse de synergie à l'AnalystAgent.
    """

    def __init__(
        self,
        gw2_client: Optional[GW2APIClient] = None,
        analyst_agent: Optional[AnalystAgent] = None,
        optimizer: Optional[object] = None,
        advisor_agent: Optional[BuildAdvisorAgent] = None,
    ) -> None:
        self.gw2_client = gw2_client or GW2APIClient()
        self.analyst_agent = analyst_agent or AnalystAgent()
        # Optimizer & advisor for equipment recommendations (optional in V1)
        self.optimizer = optimizer or get_build_optimizer()
        self.build_advisor = advisor_agent or BuildAdvisorAgent()

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

    def _estimate_skill_damage_berserker(self, skill: Dict[str, Any]) -> Optional[float]:
        power = 2500
        facts = skill.get("facts")
        if not isinstance(facts, list):
            return None

        total = 0.0
        found = False
        for f in facts:
            if not isinstance(f, dict):
                continue
            if f.get("type") != "Damage":
                continue

            coeff = f.get("dmg_multiplier")
            if not isinstance(coeff, (int, float)):
                continue

            hit_count = f.get("hit_count")
            if not isinstance(hit_count, (int, float)):
                hit_count = 1

            per_hit = calculate_damage(
                power=power,
                weapon_strength=WEAPON_STRENGTH_AVG,
                coefficient=float(coeff),
                armor=ARMOR_HEAVY,
            )
            total += per_hit * float(hit_count)
            found = True

        if not found:
            return None

        return total

    def _detect_role_from_gw2_data(
        self,
        spec_data: Optional[Dict[str, Any]],
        traits_data: List[Dict[str, Any]],
        skills_data: List[Dict[str, Any]],
        context: str,
    ) -> Optional[str]:
        """Tente de déduire un rôle global (support/boon/tank/dps) depuis les données GW2.

        Heuristique simple mais data-driven, basée sur les noms/descriptions et facts.
        On retourne None si aucun signal clair n'est trouvé, pour laisser le contexte
        texte (_derive_role_from_context) prendre le relais.
        """

        ctx = (context or "").lower()

        def _text_from(obj: Dict[str, Any]) -> str:
            parts = []
            for key in ("name", "description"):
                val = obj.get(key)
                if isinstance(val, str):
                    parts.append(val.lower())
            # On ajoute aussi les facts textuels si présents
            for facts_key in ("facts", "traited_facts"):
                facts = obj.get(facts_key)
                if isinstance(facts, list):
                    for f in facts:
                        if isinstance(f, dict):
                            t = f.get("text")
                            if isinstance(t, str):
                                parts.append(t.lower())
            return " \n".join(parts)

        heal_score = 0
        boon_score = 0
        tank_score = 0

        # Signals from specialization
        if spec_data:
            spec_txt = _text_from(spec_data)
            if any(k in spec_txt for k in ["heal", "healing", "barrier", "mender", "salvation"]):
                heal_score += 3
            if any(k in spec_txt for k in ["quickness", "alacrity", "boon duration", "concentration"]):
                boon_score += 3
            if any(k in spec_txt for k in ["tank", "defensive", "protection", "aegis", "toughness", "vitality"]):
                tank_score += 2

        # Signals from traits
        for t in traits_data:
            txt = _text_from(t)
            if any(k in txt for k in ["heal", "healing", "barrier", "revive", "resurrect"]):
                heal_score += 1
            if any(k in txt for k in ["quickness", "alacrity", "boon", "might", "fury", "stability"]):
                boon_score += 1
            if any(k in txt for k in ["toughness", "vitality", "barrier", "protection"]):
                tank_score += 1

        # Signals from skills
        for s in skills_data:
            txt = _text_from(s)
            if any(k in txt for k in ["heal", "healing", "barrier", "revive", "resurrect"]):
                heal_score += 1
            if any(k in txt for k in ["quickness", "alacrity", "boon", "might", "fury", "stability"]):
                boon_score += 1
            if any(k in txt for k in ["toughness", "vitality", "block", "aegis", "protection"]):
                tank_score += 1

        # Petit bonus si le contexte texte parle explicitement de heal/boons/tank
        if any(k in ctx for k in ["heal", "healer", "soins", "support"]):
            heal_score += 1
        if any(k in ctx for k in ["boon", "alac", "quickness"]):
            boon_score += 1
        if any(k in ctx for k in ["tank", "frontline", "stab"]):
            tank_score += 1

        # Normalisation grossière : si toutes les scores sont nuls, abandonner
        if heal_score == boon_score == tank_score == 0:
            return None

        # Choisir le score dominant si suffisamment distinct
        scores = {"support": heal_score, "boon": boon_score, "tank": tank_score}
        best_role, best_score = max(scores.items(), key=lambda kv: kv[1])
        # Vérifier qu'il n'est pas ex aequo avec un autre
        if list(scores.values()).count(best_score) > 1:
            return None

        return best_role

    def _get_stat_presets_for_role(self, role_cat: str) -> List[tuple[str, Dict[str, int]]]:
        """Retourne plusieurs presets de stats réalistes pour un rôle donné.

        Aligne la logique sur TeamCommanderAgent._get_stat_presets_for_role,
        mais avec un rôle simplifié ("dps", "heal", "boon", "tank", "support").
        """
        r = role_cat.lower()
        if r in {"dps", "strip"}:
            # DPS: presets classiques + une option plus tanky (Valkyrie)
            names = ["Berserker", "Marauder", "Dragon", "Valkyrie"]
        elif r in {"heal", "support", "cleanse"}:
            names = ["Minstrel", "Harrier", "Cleric", "Magi"]
        elif r == "boon":
            names = ["Diviner", "Minstrel", "Harrier"]
        else:
            # Tank / fallback support: ajouter quelques variantes plus "off-meta" (Trailblazer/Dire)
            names = ["Minstrel", "Soldier", "Trailblazer", "Dire"]

        filtered_names = filter_prefix_names_by_itemstats(names)
        return [(name, get_prefix_stats(name)) for name in filtered_names]

    def _derive_mode_and_experience_from_context(self, context: str) -> tuple[str, str]:
        """Déduit un mode WvW et un niveau d'expérience à partir du contexte texte.

        Pour l'instant:
          - mode: wvw_zerg / wvw_outnumber / wvw_roam
          - experience: beginner / intermediate / expert (par défaut: intermediate)
        """
        ctx = (context or "").lower()

        # Mode
        if "roam" in ctx:
            mode = "wvw_roam"
        elif "outnumber" in ctx or "out-number" in ctx:
            mode = "wvw_outnumber"
        else:
            mode = "wvw_zerg"

        # Niveau d'expérience: heuristique simple pour V1
        if "debutant" in ctx or "beginner" in ctx:
            experience = "beginner"
        elif "expert" in ctx:
            experience = "expert"
        else:
            experience = "intermediate"

        return mode, experience

    def _derive_role_from_context(self, context: str) -> str:
        """Déduit un rôle global à optimiser à partir du contexte texte.

        Heuristique simple pour V1:
          - Si le contexte mentionne heal/soins/support -> "heal" ou "support".
          - Si le contexte mentionne boon/alac/quick -> "boon".
          - Si le contexte mentionne tank/frontline -> "tank".
          - Sinon: "dps".
        """
        ctx = (context or "").lower()

        if any(k in ctx for k in ["heal", "healer", "soins", "support"]):
            # Support/Heal: on laisse BuildAdvisor affiner entre heal/support
            return "support"
        if any(k in ctx for k in ["boon", "alac", "quickness"]):
            return "boon"
        if any(k in ctx for k in ["tank", "frontline", "stab"]):
            return "tank"
        return "dps"

    async def analyze_build_synergy(
        self,
        specialization_id: Optional[int],
        trait_ids: List[int],
        skill_ids: List[int],
        context: str = "WvW Zerg",
        equipment_summary: Optional[Dict[str, Any]] = None,
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
            view = self._minify_gw2_object(s, extra_fields=["type", "slot", "flags"])
            estimated = self._estimate_skill_damage_berserker(s)
            if estimated is not None:
                view["estimated_damage_berserker"] = estimated
            skills_view.append(view)

        # Détection de rôle data-driven (support/boon/tank) avec fallback sur le contexte
        detected_role = self._detect_role_from_gw2_data(spec_data, traits_data, skills_data, context)
        if detected_role is None:
            detected_role = self._derive_role_from_context(context)

        build_payload: Dict[str, Any] = {
            "context": context,
            "specialization": spec_view,
            "traits": traits_view,
            "skills": skills_view,
            "detected_role": detected_role,
        }

        if equipment_summary:
            build_payload["equipment_summary"] = equipment_summary

        # ==================== Delegate to AnalystAgent ====================
        envelope = await self.analyst_agent.execute({"build_data": build_payload, "context": context})
        if not envelope.get("success"):
            error = envelope.get("error") or "unknown_error"
            raise RuntimeError(f"AnalystAgent build analysis failed: {error}")

        result = envelope["result"]
        # S'assurer que le rôle détecté est remonté dans la réponse pour les consommateurs
        if isinstance(result, dict) and "detected_role" not in result:
            result["detected_role"] = detected_role
        return result

    async def analyze_build_full(
        self,
        specialization_id: Optional[int],
        trait_ids: List[int],
        skill_ids: List[int],
        context: str = "WvW Zerg",
        equipment_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyse complète d'un build: synergie IA + optimisation d'équipement.

        Cette méthode orchestre d'abord l'analyse de synergie classique
        (AnalystAgent) puis effectue une optimisation d'équipement orientée DPS
        via BuildEquipmentOptimizer + BuildAdvisorAgent.
        """

        # 1) Analyse de synergie via AnalystAgent (LLM)
        synergy_result = await self.analyze_build_synergy(
            specialization_id=specialization_id,
            trait_ids=trait_ids,
            skill_ids=skill_ids,
            context=context,
            equipment_summary=equipment_summary,
        )

        # 2) Optimisation d'équipement (optionnelle)
        gear_optimization: Optional[Dict[str, Any]] = None

        try:
            mode, experience = self._derive_mode_and_experience_from_context(context)
            # Privilégier le rôle détecté via les données GW2 si présent, sinon fallback contexte
            role_cat = None
            if isinstance(synergy_result, dict):
                role_cat = synergy_result.get("detected_role")
            if not isinstance(role_cat, str) or not role_cat:
                role_cat = self._derive_role_from_context(context)

            # Placeholder de rotation: même logique que TeamCommanderAgent
            skill_rotation = [
                {"name": "Burst 1", "damage_coefficient": 2.0},
                {"name": "Burst 2", "damage_coefficient": 1.5},
                {"name": "Auto Attack", "damage_coefficient": 0.8},
            ]

            stat_presets = self._get_stat_presets_for_role(role_cat)
            candidates: List[BuildCandidate] = []
            results_by_id: Dict[str, OptimizationResult] = {}

            for idx, (preset_name, base_stats) in enumerate(stat_presets):
                try:
                    opt = await self.optimizer.optimize_build(
                        base_stats=base_stats,
                        skill_rotation=skill_rotation,
                        role=role_cat,
                    )
                except Exception as e:  # pragma: no cover - robust à l'échec isolé
                    logger.error(f"Build optimization failed for preset {preset_name}: {e}")
                    continue

                candidate_id = f"{preset_name}-{idx}"
                results_by_id[candidate_id] = opt
                candidates.append(
                    BuildCandidate(
                        id=candidate_id,
                        prefix=preset_name,
                        role=role_cat,
                        rune=opt.rune_name,
                        sigils=opt.sigil_names,
                        total_damage=opt.total_damage,
                        survivability=opt.survivability_score,
                        overall_score=opt.overall_score,
                    )
                )

            if candidates:
                decision: AdvisorChoice = self.build_advisor.choose_best_candidate(
                    candidates=candidates,
                    role=role_cat,
                    context={"mode": mode, "experience": experience},
                )
                advised = decision.candidate
                ranked = decision.ranked_candidates or []

                best_result = results_by_id.get(advised.id)
                if best_result is None:
                    # Fallback: max overall_score si l'ID ne correspond pas
                    best_result = max(results_by_id.values(), key=lambda r: r.overall_score)

                alts: List[Dict[str, Any]] = []
                for cand in ranked:
                    if cand.id == advised.id:
                        continue
                    alts.append(
                        {
                            "prefix": cand.prefix,
                            "rune": cand.rune,
                            "sigils": list(cand.sigils),
                            "total_damage": cand.total_damage,
                            "survivability": cand.survivability,
                            "overall_score": cand.overall_score,
                        }
                    )
                gear_optimization = {
                    "role": role_cat,
                    "experience": experience,
                    "mode": mode,
                    "chosen": {
                        "prefix": advised.prefix,
                        "rune": best_result.rune_name,
                        "sigils": best_result.sigil_names,
                        "total_damage": best_result.total_damage,
                        "survivability": best_result.survivability_score,
                        "overall_score": best_result.overall_score,
                        "reason": decision.reason,
                    },
                    "alternatives": alts,
                }

        except Exception as e:  # pragma: no cover - ne doit pas casser la synergie
            logger.error(f"Gear optimization in analyze_build_full failed: {e}")
            gear_optimization = None

        # 3) Retourner un payload combiné pour le frontend
        full_result: Dict[str, Any] = dict(synergy_result)
        if gear_optimization is not None:
            full_result["gear_optimization"] = gear_optimization
        return full_result
