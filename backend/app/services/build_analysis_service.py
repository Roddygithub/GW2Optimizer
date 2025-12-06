from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from app.core.logging import logger
from app.core.config import settings
from app.services.gw2_api_client import GW2APIClient
from app.services.gw2_data_service import Gw2DataService, get_gw2_data_service, RoleAnalysis
from app.agents.analyst_agent import AnalystAgent
from app.engine.damage import ARMOR_HEAVY, WEAPON_STRENGTH_AVG, calculate_damage
from app.agents.build_equipment_optimizer import get_build_optimizer, OptimizationResult
from app.engine.gear.prefixes import get_prefix_stats, PREFIX_REGISTRY, get_all_prefixes
from app.engine.gear.registry import RUNE_REGISTRY, RELIC_REGISTRY
from app.agents.build_advisor_agent import BuildAdvisorAgent, BuildCandidate, AdvisorChoice
from app.services.gear_prefix_validator import filter_prefix_names_by_itemstats
from app.services.gear_preset_service import get_gear_preset_service
from app.services.meta_build_catalog import (
    load_meta_builds_from_json,
    find_meta_build_by_chat_code,
    MetaBuild,
)
from app.services.meta_rag_service import MetaRAGService
from app.engine.simulation.rotation import get_firebrand_support_wvw_rotation, get_reaper_power_wvw_rotation


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
        gw2_data_service: Optional[Gw2DataService] = None,
    ) -> None:
        self.gw2_client = gw2_client or GW2APIClient()
        self.analyst_agent = analyst_agent or AnalystAgent()
        # Optimizer & advisor for equipment recommendations (optional in V1)
        self.optimizer = optimizer or get_build_optimizer()
        self.build_advisor = advisor_agent or BuildAdvisorAgent()
        # GW2 Data Service for intelligent role detection and meta context
        self.gw2_data_service = gw2_data_service or get_gw2_data_service()
        # Meta RAG service to retrieve external meta builds for prompts
        self.meta_rag = MetaRAGService()
        self._current_meta_snapshot: Optional[Dict[str, Any]] = self._load_current_meta_snapshot()
        self._meta_builds_raw: Optional[Dict[str, Any]] = self._load_meta_builds_raw()

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

        # Normalisation grossière : si tous les scores sont nuls, abandonner et laisser le contexte texte décider
        if heal_score == boon_score == tank_score == 0:
            return None

        # Choisir le score dominant avec une stratégie explicite en cas d'égalité.
        # On préfère généralement les rôles orientés support/boon plutôt que "dps" implicite.
        scores = {"support": heal_score, "boon": boon_score, "tank": tank_score}
        best_score = max(scores.values())

        # Rôles co-leaders (égalité sur le meilleur score)
        best_roles = [role for role, score in scores.items() if score == best_score]
        if len(best_roles) == 1:
            return best_roles[0]

        # En cas d'égalité, appliquer un ordre de priorité stable
        for preferred in ("support", "boon", "tank"):
            if preferred in best_roles:
                return preferred

        # Fallback défensif (ne devrait pas être atteint)
        return best_roles[0]

    def _get_stat_presets_for_role(self, role_cat: str) -> List[tuple[str, Dict[str, int]]]:
        """Retourne plusieurs presets de stats réalistes pour un rôle donné.

        Aligne la logique sur TeamCommanderAgent._get_stat_presets_for_role,
        mais avec un rôle simplifié ("dps", "heal", "boon", "tank", "support").
        """
        r = role_cat.lower()

        # Utiliser toutes les stats connues via itemstats.json pour découvrir
        # dynamiquement les presets adaptés à chaque rôle.
        all_prefixes = get_all_prefixes()

        def _is_dps(stats: Dict[str, int]) -> bool:
            return stats.get("power", 0) >= 800 and stats.get("precision", 0) >= 800

        def _is_boon_heal(stats: Dict[str, int]) -> bool:
            return stats.get("healing_power", 0) >= 800 and stats.get("concentration", 0) >= 800

        def _is_heal_support(stats: Dict[str, int]) -> bool:
            return stats.get("healing_power", 0) >= 800 or stats.get("concentration", 0) >= 800

        def _is_boon(stats: Dict[str, int]) -> bool:
            return stats.get("concentration", 0) >= 800

        def _is_tank(stats: Dict[str, int]) -> bool:
            return stats.get("toughness", 0) >= 1200 and stats.get("vitality", 0) >= 1200

        names: List[str]

        if r in {"dps", "strip"}:
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_dps(stats)
            ]
            if not names:
                names = ["Berserker", "Marauder", "Dragon", "Valkyrie"]
        elif r in {"heal", "support", "cleanse"}:
            candidates = [
                name
                for name, stats in all_prefixes.items()
                if _is_boon_heal(stats) or _is_heal_support(stats)
            ]
            if candidates:
                names = sorted(set(candidates))
            else:
                names = ["Minstrel", "Harrier", "Cleric", "Magi"]
        elif r == "boon":
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_boon(stats)
            ]
            if not names:
                names = ["Diviner", "Minstrel", "Harrier"]
        else:
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_tank(stats)
            ]
            if not names:
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

    def _build_synergy_fallback_result(
        self,
        context: str,
        detected_role: str,
        build_payload: Dict[str, Any],
        error: str | None = None,
    ) -> Dict[str, Any]:
        """Construit un résultat de synergie déterministe sans appel à Ollama.

        Utilisé lorsque l'AnalystAgent échoue et que AI_FALLBACK_ENABLED est activé.
        """

        summary_parts = [
            f"Analyse de synergie basée sur les données locales pour un build orienté {detected_role} en {context}.",
        ]
        if error:
            summary_parts.append("Résultat généré via fallback après échec de l'IA distante.")

        summary = " ".join(summary_parts)

        return {
            "context": context,
            "synergy_score": "B",
            "strengths": [
                f"Profil cohérent pour le rôle {detected_role} dans le contexte {context}.",
            ],
            "weaknesses": [],
            "summary": summary,
            "raw_response": {
                "fallback": "offline_rule_based",
                "error": error,
            },
            "build_data": build_payload,
            "detected_role": detected_role,
        }

    def _select_skill_rotation_for_build(
        self,
        synergy_result: Dict[str, Any],
        role_cat: str,
    ) -> List[Dict[str, Any]]:
        """Choisit une rotation de skills pour l'optimizer en fonction du build.

        Par défaut, on utilise une petite rotation générique Burst 1 / Burst 2 /
        Auto-attack. Pour certains archétypes bien identifiés (par ex. Firebrand
        support WvW), on peut substituer une rotation plus réaliste pour la
        simulation de rotation (RotationSimulator) sans changer la logique
        globale de score (burst + survie).
        """

        # Rotation générique utilisée historiquement pour tous les builds
        default_rotation: List[Dict[str, Any]] = [
            {"name": "Burst 1", "damage_coefficient": 2.0},
            {"name": "Burst 2", "damage_coefficient": 1.5},
            {"name": "Auto Attack", "damage_coefficient": 0.8},
        ]

        try:
            if not isinstance(synergy_result, dict):
                return default_rotation

            build_data = synergy_result.get("build_data")
            if not isinstance(build_data, dict):
                return default_rotation

            spec = build_data.get("specialization")
            if not isinstance(spec, dict):
                return default_rotation

            profession = str(spec.get("profession") or "").lower()
            spec_name = str(spec.get("name") or "").lower()
            normalized_role = str(role_cat or "").lower()

            # Firebrand support / boon WvW: utiliser une rotation dédiée
            if profession == "guardian" and "firebrand" in spec_name:
                if normalized_role in {"support", "boon", "heal"}:
                    return get_firebrand_support_wvw_rotation()

            # Reaper power DPS WvW: utiliser une rotation dédiée
            if profession == "necromancer" and "reaper" in spec_name:
                if normalized_role in {"dps"}:
                    return get_reaper_power_wvw_rotation()

        except Exception:
            # En cas de problème de données, on retombe silencieusement sur la rotation par défaut
            return default_rotation

        return default_rotation

    def _detect_meta_build_match(self, chat_code: Optional[str], context: str) -> Optional[MetaBuild]:
        if not chat_code:
            return None
        base_dir = Path(__file__).resolve().parent.parent
        json_path = base_dir / "data" / "learning" / "external" / "meta_builds_wvw.json"
        try:
            loaded = load_meta_builds_from_json(str(json_path))
        except Exception as e:
            logger.error("Failed to load meta builds registry", extra={"error": str(e)})
            return None
        if loaded <= 0:
            return None
        try:
            return find_meta_build_by_chat_code(chat_code)
        except Exception as e:
            logger.error("Failed to match meta build by chat code", extra={"error": str(e)})
            return None

    def _build_meta_comparison_payload(
        self,
        meta_build: MetaBuild,
        gear_optimization: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": meta_build.id,
            "name": meta_build.name,
            "source": meta_build.source,
            "game_mode": meta_build.game_mode,
            "role": meta_build.role,
            "profession": meta_build.profession,
            "specialization": meta_build.specialization,
            "runes_text": meta_build.runes_text,
            "stats_text": meta_build.stats_text,
        }

        optimizer_rune: Optional[str] = None
        if isinstance(gear_optimization, dict):
            chosen = gear_optimization.get("chosen")
            if isinstance(chosen, dict):
                r = chosen.get("rune")
                if isinstance(r, str) and r:
                    optimizer_rune = r

        meta_rune: Optional[str] = None
        if isinstance(meta_build.runes_text, str) and meta_build.runes_text:
            lowered = meta_build.runes_text.lower()
            for rune_name in RUNE_REGISTRY.keys():
                if rune_name.lower() in lowered:
                    meta_rune = rune_name
                    break

        if optimizer_rune or meta_rune:
            payload["rune_diff"] = {
                "optimizer_rune": optimizer_rune,
                "meta_rune": meta_rune,
                "changed": bool(optimizer_rune and meta_rune and optimizer_rune != meta_rune),
            }

        optimizer_prefix: Optional[str] = None
        if isinstance(gear_optimization, dict):
            chosen = gear_optimization.get("chosen")
            if isinstance(chosen, dict):
                p = chosen.get("prefix")
                if isinstance(p, str) and p:
                    optimizer_prefix = p

        meta_prefix: Optional[str] = None
        if isinstance(meta_build.stats_text, str) and meta_build.stats_text:
            lowered_stats = meta_build.stats_text.lower()
            for prefix_name in PREFIX_REGISTRY.keys():
                if prefix_name.lower() in lowered_stats:
                    meta_prefix = prefix_name
                    break

        if optimizer_prefix or meta_prefix:
            payload["stats_diff"] = {
                "optimizer_prefix": optimizer_prefix,
                "meta_prefix": meta_prefix,
                "changed": bool(
                    optimizer_prefix and meta_prefix and optimizer_prefix != meta_prefix
                ),
            }

        optimizer_relic: Optional[str] = None
        if isinstance(gear_optimization, dict):
            chosen = gear_optimization.get("chosen")
            if isinstance(chosen, dict):
                rr = chosen.get("relic")
                if isinstance(rr, str) and rr:
                    optimizer_relic = rr

        meta_relic: Optional[str] = None
        combined_text_parts = []
        if isinstance(meta_build.stats_text, str) and meta_build.stats_text:
            combined_text_parts.append(meta_build.stats_text)
        if isinstance(meta_build.runes_text, str) and meta_build.runes_text:
            combined_text_parts.append(meta_build.runes_text)
        if combined_text_parts:
            lowered = " ".join(combined_text_parts).lower()
            for relic_name in RELIC_REGISTRY.keys():
                if relic_name.lower() in lowered:
                    meta_relic = relic_name
                    break

        if optimizer_relic or meta_relic:
            payload["relic_diff"] = {
                "optimizer_relic": optimizer_relic,
                "meta_relic": meta_relic,
                "changed": bool(
                    optimizer_relic and meta_relic and optimizer_relic != meta_relic
                ),
            }

        return payload

    def _load_current_meta_snapshot(self) -> Optional[Dict[str, Any]]:
        base_dir = Path(__file__).resolve().parent.parent
        path = base_dir / "data" / "learning" / "external" / "current_meta.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to load current_meta.json", extra={"error": str(e)})
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _load_meta_builds_raw(self) -> Optional[Dict[str, Any]]:
        base_dir = Path(__file__).resolve().parent.parent
        path = base_dir / "data" / "learning" / "external" / "meta_builds_wvw.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Failed to load meta_builds_wvw.json", extra={"error": str(e)})
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _build_meta_context_snippet(
        self,
        profession: Optional[str],
        context: str,
    ) -> Optional[str]:
        lines: List[str] = []

        # Derive WvW mode (zerg/outnumber/roam)
        mode, _ = self._derive_mode_and_experience_from_context(context)
        if mode == "wvw_roam":
            mode_short = "roam"
        elif mode == "wvw_outnumber":
            mode_short = "outnumber"
        else:
            mode_short = "zerg"

        # High-level snapshot from current_meta.json
        snapshot = self._current_meta_snapshot or {}
        trending = snapshot.get("trending") if isinstance(snapshot, dict) else None
        if isinstance(trending, dict):
            builds = trending.get("builds") or []
            if isinstance(builds, list):
                names: List[str] = []
                for entry in builds:
                    if not isinstance(entry, dict):
                        continue
                    if profession and entry.get("profession") != profession:
                        continue
                    if entry.get("mode") != mode_short:
                        continue
                    name = entry.get("name")
                    if isinstance(name, str):
                        names.append(name)
                if names:
                    lines.append(
                        f"Méta publique ({mode_short}) pour {profession or 'toutes professions'}: builds tendances externes: "
                        + ", ".join(sorted(set(names))[:5])
                    )

            by_mode = trending.get("by_mode") or {}
            if isinstance(by_mode, dict):
                mode_entry = by_mode.get(mode_short)
                if isinstance(mode_entry, dict):
                    top_profs = mode_entry.get("top_professions") or []
                    if isinstance(top_profs, list) and top_profs:
                        lines.append(
                            f"Professions les plus jouées en WvW {mode_short}: "
                            + ", ".join(str(p) for p in top_profs[:5])
                        )

        # Concrete examples from meta_builds_wvw.json
        raw_meta = self._meta_builds_raw or {}
        builds_list = raw_meta.get("builds") if isinstance(raw_meta, dict) else None
        if isinstance(builds_list, list):
            candidates: List[str] = []
            for entry in builds_list:
                if not isinstance(entry, dict):
                    continue
                if profession and entry.get("profession") != profession:
                    continue
                gm = str(entry.get("game_mode") or "")
                if mode not in gm:
                    continue
                name = entry.get("name")
                source = entry.get("source")
                if isinstance(name, str):
                    label = name
                    if isinstance(source, str) and source:
                        label = f"{name} ({source})"
                    candidates.append(label)
            if candidates:
                lines.append(
                    f"Exemples de builds WvW référencés pour {profession or 'toutes professions'} en {mode_short}: "
                    + ", ".join(sorted(set(candidates))[:5])
                )

        if not lines:
            return None

        text = "\n".join(lines)
        # Limiter la taille du contexte méta pour rester léger
        return text[:800]

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
        # Use Gw2DataService for enriched meta context when possible,
        # then enrich with MetaRAGService snippets.
        meta_context: Optional[str] = None
        mode, _ = self._derive_mode_and_experience_from_context(context)
        game_mode = "wvw" if "wvw" in mode else "pve"
        spec_name: Optional[str] = None
        if spec_data:
            raw_name = spec_data.get("name")
            if isinstance(raw_name, str) and raw_name:
                spec_name = raw_name

        try:
            meta_context = self.gw2_data_service.get_meta_context_string(
                game_mode=game_mode,
                profession=spec_profession,
                specialization=spec_name,
                role=None,  # Will be detected later
                user_build_data=None,
            )
        except Exception as e:
            logger.warning(f"Gw2DataService meta context failed, using legacy: {e}")
            meta_context = self._build_meta_context_snippet(spec_profession, context)

        # Always try to enrich meta_context with RAG snippets based on
        # external meta builds (Hardstuck, Snowcrows, GuildJen, etc.).
        try:
            rag_context = self.meta_rag.build_context_for_build(
                game_mode=game_mode,
                profession=spec_profession,
                specialization=spec_name,
                role=None,
                question=context,
            )
            if rag_context:
                if meta_context:
                    meta_context = f"{meta_context}\n\n{rag_context}"
                else:
                    meta_context = rag_context
        except Exception as e:  # pragma: no cover - guardrail
            logger.warning("MetaRAGService meta context failed", extra={"error": str(e)})
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

        # Détection de rôle intelligente via Gw2DataService
        role_analysis: Optional[RoleAnalysis] = None
        try:
            role_analysis = self.gw2_data_service.detect_role(
                spec_id=specialization_id,
                trait_ids=trait_ids,
                skill_ids=skill_ids,
                context=context,
            )
            detected_role = role_analysis.primary_role
            logger.info(
                f"Intelligent role detection: {detected_role} (confidence: {role_analysis.confidence:.2f})",
                extra={"secondary_roles": role_analysis.secondary_roles},
            )
        except Exception as e:
            logger.warning(f"Gw2DataService role detection failed, falling back: {e}")
            # Fallback to legacy detection
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
        if meta_context:
            inputs: Dict[str, Any] = {"build_data": build_payload, "context": context, "meta_context": meta_context}
        else:
            inputs = {"build_data": build_payload, "context": context}

        envelope = await self.analyst_agent.execute(inputs)
        if not envelope.get("success"):
            error_text = str(envelope.get("error") or "unknown_error")
            logger.error(
                "AnalystAgent build analysis failed, using fallback if enabled",
                extra={"error": error_text},
            )
            if settings.AI_FALLBACK_ENABLED:
                return self._build_synergy_fallback_result(
                    context=context,
                    detected_role=detected_role,
                    build_payload=build_payload,
                    error=error_text,
                )
            raise RuntimeError(f"AnalystAgent build analysis failed: {error_text}")

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
        chat_code: Optional[str] = None,
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

            # Choix de la rotation de skills pour l'optimizer (peut être spécialisée
            # pour certains archétypes comme Firebrand support WvW)
            skill_rotation = self._select_skill_rotation_for_build(
                synergy_result=synergy_result,
                role_cat=role_cat,
            )

            stat_presets = self._get_stat_presets_for_role(role_cat)
            candidates: List[BuildCandidate] = []
            results_by_id: Dict[str, OptimizationResult] = {}

            opt = self.optimizer
            if hasattr(opt, "set_mode"):
                try:
                    opt.set_mode(mode)
                except Exception:
                    pass

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
                        relic=opt.relic_name,
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
                            "relic": cand.relic,
                        }
                    )
                example_armor: List[Dict[str, Any]] = []
                try:
                    preset_service = get_gear_preset_service()
                    armor_items = preset_service.get_example_armor_for_prefix(advised.prefix)
                    if armor_items:
                        example_armor = [item.model_dump() for item in armor_items]
                except Exception:
                    example_armor = []

                chosen_payload: Dict[str, Any] = {
                    "prefix": advised.prefix,
                    "rune": best_result.rune_name,
                    "sigils": best_result.sigil_names,
                    "relic": best_result.relic_name,
                    "total_damage": best_result.total_damage,
                    "survivability": best_result.survivability_score,
                    "overall_score": best_result.overall_score,
                    "reason": decision.reason,
                }
                # Exposer les métriques de rotation issues du moteur de simulation avancée
                try:
                    br = getattr(best_result, "breakdown", None)
                    if isinstance(br, dict):
                        rot_dps = br.get("rotation_dps_10s")
                        rot_total = br.get("rotation_total_damage_10s")
                        rot_hps = br.get("rotation_hps_10s")
                        rot_heal_total = br.get("rotation_total_heal_10s")
                        if rot_dps is not None:
                            chosen_payload["rotation_dps_10s"] = rot_dps
                        if rot_total is not None:
                            chosen_payload["rotation_total_damage_10s"] = rot_total
                        if rot_hps is not None:
                            chosen_payload["rotation_hps_10s"] = rot_hps
                        if rot_heal_total is not None:
                            chosen_payload["rotation_total_heal_10s"] = rot_heal_total
                except Exception:
                    # Ne jamais casser l'analyse complète pour une simple métrique de debug
                    pass
                if example_armor:
                    chosen_payload["example_armor"] = example_armor

                gear_optimization = {
                    "role": role_cat,
                    "experience": experience,
                    "mode": mode,
                    "chosen": chosen_payload,
                    "alternatives": alts,
                }

        except Exception as e:  # pragma: no cover - ne doit pas casser la synergie
            logger.error(f"Gear optimization in analyze_build_full failed: {e}")
            gear_optimization = None

        # Meta comparison using Gw2DataService intelligent comparison
        meta_comparison: Optional[Dict[str, Any]] = None
        try:
            # Use the new intelligent meta comparison from Gw2DataService
            meta_comparison = self.gw2_data_service.compare_build_to_meta(
                spec_id=specialization_id,
                trait_ids=trait_ids,
                skill_ids=skill_ids,
                gear_optimization=gear_optimization,
                context=context,
            )
            
            # Add similarity score to the result for frontend display
            if meta_comparison and meta_comparison.get("closest_meta"):
                logger.info(
                    f"Meta comparison: {meta_comparison['closest_meta']['name']} "
                    f"(similarity: {meta_comparison['similarity_score']:.2f})"
                )
            
            # Also try legacy chat_code matching if available
            if chat_code:
                legacy_match = self._detect_meta_build_match(chat_code=chat_code, context=context)
                if legacy_match is not None:
                    legacy_payload = self._build_meta_comparison_payload(legacy_match, gear_optimization)
                    if meta_comparison:
                        meta_comparison["chat_code_match"] = legacy_payload
                    else:
                        meta_comparison = legacy_payload
        except Exception as e:
            logger.error("Meta comparison in analyze_build_full failed", extra={"error": str(e)})
            meta_comparison = None

        # 3) Retourner un payload combiné pour le frontend
        full_result: Dict[str, Any] = dict(synergy_result)
        if gear_optimization is not None:
            full_result["gear_optimization"] = gear_optimization
        if chat_code:
            full_result["chat_code"] = chat_code
        if meta_comparison is not None:
            full_result["meta_comparison"] = meta_comparison
        return full_result
