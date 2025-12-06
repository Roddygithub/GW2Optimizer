"""
Team Commander Agent - IA Chef d'Orchestre pour WvW Teams

Cet agent interpète des requêtes naturelles comme:
  "Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"

Et construit automatiquement une team complète avec:
  - Builds optimisés (traits, skills, gear)
  - Runes et sigils auto-sélectionnés
  - Analyse de synergie globale

VISION: L'utilisateur parle, l'IA fait TOUT.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from app.core.logging import logger
from app.core.performance import async_timed, batch_processor, async_timer
from app.agents.build_equipment_optimizer import get_build_optimizer, OptimizationResult
from app.engine.combat.context import CombatContext
from app.engine.gear.prefixes import get_prefix_stats, get_all_prefixes
from app.agents.build_advisor_agent import BuildAdvisorAgent, BuildCandidate
from app.agents.team_strategy_agent import TeamStrategyAgent
from app.models.team_strategy import TeamStrategyPlan, TeamStrategyRequest
from app.services.gear_prefix_validator import filter_prefix_names_by_itemstats
from app.services.gear_optimization_service import get_gear_optimization_service
from app.services.meta_rag_service import MetaRAGService


class Role(str, Enum):
    """Rôles possibles dans un groupe WvW."""
    STAB = "stab"  # Stabilité
    HEAL = "heal"  # Soins
    BOON = "boon"  # Boon share (Might, Alacrity, etc.)
    STRIP = "strip"  # Boon strip / corruption
    DPS = "dps"  # Damage pur
    TANK = "tank"  # Frontline tank
    SUPPORT = "support"  # Support général
    CLEANSE = "cleanse"  # Condi cleanse


@dataclass
class TeamRequest:
    """Structure d'une requête de team."""
    team_size: int
    groups: int
    roles_per_group: List[Role]
    constraints: Dict[str, Any]  # Ex: {"classes": ["Firebrand", "Druid"]}
    user_message: str  # Message original
    experience: str  # beginner, intermediate, expert
    mode: str  # wvw_zerg, wvw_outnumber, wvw_roam


@dataclass
class SlotBuild:
    """Build complet pour un slot."""
    role: Role
    profession: str
    specialization: str
    rune: str
    sigils: List[str]
    stats_priority: str  # "Berserker", "Minstrel", etc.
    performance: Dict[str, float]  # DPS, heal, survivability
    advisor_reason: Optional[str] = None
    advisor_alternatives: Optional[List[Dict[str, Any]]] = None
    relic: Optional[str] = None
    gear_mix: Optional[Dict[str, str]] = None


@dataclass
class TeamGroup:
    """Un groupe de 5 joueurs."""
    index: int
    slots: List[SlotBuild]


@dataclass
class TeamResult:
    """Résultat complet de la génération de team."""
    groups: List[TeamGroup]
    synergy_score: str  # S, A, B, C
    synergy_details: Dict[str, str]
    notes: List[str]


class TeamCommanderAgent:
    """
    Agent chef d'orchestre pour créer des teams WvW complètes.
    
    Usage:
        agent = TeamCommanderAgent()
        result = await agent.run("Je veux 2 groupes de 5 avec Firebrand, Druid...")
    """
    
    # Mapping rôle → classes WvW meta
    ROLE_TO_CLASSES = {
        Role.STAB: ["Guardian Firebrand", "Mesmer Chronomancer"],
        Role.HEAL: ["Ranger Druid", "Engineer Scrapper", "Elementalist Tempest"],
        Role.BOON: ["Revenant Herald", "Mesmer Chronomancer", "Guardian Firebrand"],
        Role.STRIP: ["Warrior Spellbreaker", "Necromancer Scourge", "Mesmer Mirage"],
        Role.DPS: [
            "Necromancer Reaper", "Necromancer Harbinger", "Warrior Berserker",
            "Thief Deadeye", "Engineer Holosmith", "Guardian Willbender"
        ],
        Role.TANK: ["Guardian Firebrand", "Warrior Spellbreaker"],
        Role.SUPPORT: ["Engineer Scrapper", "Ranger Druid", "Guardian Firebrand"],
        Role.CLEANSE: ["Engineer Scrapper", "Ranger Druid", "Necromancer Scourge"],
    }
    
    # Mapping classe → profession (pour GW2 API)
    CLASS_TO_PROFESSION = {
        "Guardian": "Guardian",
        "Warrior": "Warrior",
        "Engineer": "Engineer",
        "Ranger": "Ranger",
        "Thief": "Thief",
        "Elementalist": "Elementalist",
        "Mesmer": "Mesmer",
        "Necromancer": "Necromancer",
        "Revenant": "Revenant",
    }
    
    def __init__(self, meta_rag: Optional[MetaRAGService] = None):
        self.optimizer = get_build_optimizer()
        self.build_advisor = BuildAdvisorAgent()
        self.meta_rag = meta_rag or MetaRAGService()
        # Stratège LLM responsable de la composition haut niveau (classes/rôles)
        self.strategy_agent = TeamStrategyAgent(meta_rag=self.meta_rag)
        # Greedy gear solver pour le mix d'armure pièce par pièce
        self.gear_optimization_service = get_gear_optimization_service()
    
    async def run(
        self,
        message: str,
        experience: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> TeamResult:
        """
        Entry point principal.
        
        Args:
            message: Requête utilisateur (ex: "Je veux 2 groupes de 5 avec...")
        
        Returns:
            TeamResult avec groups, synergy, notes
        """
        logger.info(f"🎮 Team Commander: Parsing request: {message[:100]}...")
        
        # 1. Parse request
        request = self._parse_request(message)

        # Permettre au frontend/API de forcer le niveau d'expérience
        if experience is not None:
            request.experience = experience.lower()

        # Permettre au frontend/API de forcer le mode de jeu (zerg/outnumber/roam)
        if mode is not None:
            request.mode = mode.lower()
        
        # 2. Build team
        #    On tente d'abord la voie "AI-first" via TeamStrategyAgent.
        try:
            result = await self._build_team_with_strategy(request)
            logger.info(
                "✅ Team Commander: Team built via TeamStrategyAgent",
                extra={"mode": request.mode, "experience": request.experience},
            )
        except Exception as e:
            logger.warning(
                "TeamStrategyAgent failed, falling back to rule-based builder",
                extra={"error": str(e)},
            )
            result = await self._build_team(request)
        
        logger.info(f"✅ Team Commander: Team built successfully ({result.synergy_score})")
        
        return result
    
    def _parse_request(self, message: str) -> TeamRequest:
        """
        Parse la requête utilisateur en TeamRequest structuré.
        
        Exemples:
          "2 groupes de 5" → team_size=10, groups=2
          "Firebrand, Druid, Harbinger" → classes contraintes
        """
        message_lower = message.lower()

        # Détecter le mode de jeu à partir du message
        mode = "wvw_zerg"
        if "roam" in message_lower or "roaming" in message_lower:
            mode = "wvw_roam"
        elif "outnumber" in message_lower or "out-number" in message_lower:
            mode = "wvw_outnumber"

        # Détecter team size
        team_size = 10  # Default
        groups = 2  # Default
        
        # Pattern: "X groupes de Y"
        match = re.search(r"(\d+)\s+groupes?\s+de\s+(\d+)", message_lower)
        if match:
            groups = int(match.group(1))
            slots_per_group = int(match.group(2))
            team_size = groups * slots_per_group
        
        # Pattern: "équipe de X"
        match = re.search(r"équipe\s+de\s+(\d+)", message_lower)
        if match:
            team_size = int(match.group(1))
            # Par défaut, on considère des groupes de 5, mais on ne doit jamais descendre à 0 groupe
            groups = max(1, team_size // 5)
        
        # Détecter rôles
        roles = []
        role_keywords = {
            "stab": Role.STAB,
            "stabilité": Role.STAB,
            "stabeur": Role.STAB,
            "heal": Role.HEAL,
            "soins": Role.HEAL,
            "healer": Role.HEAL,
            "boon": Role.BOON,
            "booner": Role.BOON,
            "might": Role.BOON,
            "strip": Role.STRIP,
            "corruption": Role.STRIP,
            "dps": Role.DPS,
            "damage": Role.DPS,
            "tank": Role.TANK,
            "frontline": Role.TANK,
            "cleanse": Role.CLEANSE,
            "condi clear": Role.CLEANSE,
            "support": Role.SUPPORT,
        }
        
        for keyword, role in role_keywords.items():
            if keyword in message_lower and role not in roles:
                roles.append(role)
        
        # Si aucun rôle détecté explicitement, adapter selon le mode
        if not roles:
            if mode == "wvw_roam":
                # Petite équipe de roam : on veut au moins un support hybride
                # puis le reste en DPS roamer.
                effective_size = max(1, min(team_size, 5))
                if effective_size == 1:
                    roles = [Role.DPS]
                else:
                    roles = [Role.SUPPORT] + [Role.DPS] * (effective_size - 1)
            else:
                # Composition standard orientée zerg
                roles = [Role.STAB, Role.HEAL, Role.BOON, Role.STRIP, Role.DPS]
        
        # Détecter classes contraintes
        class_names = [
            "Firebrand", "Druid", "Herald", "Spellbreaker", "Scrapper",
            "Reaper", "Harbinger", "Berserker", "Deadeye", "Holosmith",
            "Willbender", "Chronomancer", "Mirage", "Scourge", "Tempest",
        ]
        
        constraints = {}
        detected_classes = []
        for class_name in class_names:
            if class_name.lower() in message_lower:
                detected_classes.append(class_name)
        
        if detected_classes:
            constraints["classes"] = detected_classes

        # Sécurité supplémentaire : ne jamais renvoyer moins d'un groupe
        if groups <= 0:
            groups = 1

        # Éviter d'avoir plus de rôles de base que de slots logiques
        if len(roles) > team_size:
            roles = roles[:team_size]

        return TeamRequest(
            team_size=team_size,
            groups=groups,
            roles_per_group=roles,
            constraints=constraints,
            user_message=message,
            experience="intermediate",
            mode=mode,
        )
    
    @async_timed
    async def _build_team(self, request: TeamRequest) -> TeamResult:
        """
        Construit la team complète selon le TeamRequest.
        
        OPTIMISÉ : Utilise le batch processing pour paralléliser les slots.
        
        Pour chaque slot:
          1. Choisit la classe (selon rôle et contraintes)
          2. Optimise le build (runes/sigils via BuildEquipmentOptimizer)
          3. Calcule performance
        
        Puis:
          4. Analyse synergie globale
          5. Génère notes/recommandations
        """
        logger.info(f"🔨 Building team: {request.team_size} players, {request.groups} groups")

        slots_per_group = request.team_size // request.groups
        constrained_classes = request.constraints.get("classes", [])

        # En Roaming petites équipes, on essaie de diversifier les classes par rôle
        is_small_roam = (
            isinstance(request.mode, str)
            and request.mode.lower() == "wvw_roam"
            and request.team_size <= 5
        )

        role_class_pools: dict[Role, list[str]] = {}
        role_class_idx: dict[Role, int] = {}

        def _next_class_for_role(role: Role) -> str:
            """Retourne une classe différente pour un rôle donné (en Roaming).

            On fusionne les classes issues des builds méta avec les options
            historiques ROLE_TO_CLASSES, pour éviter de répéter 3x le même
            build lorsqu'il n'y a qu'un seul hit méta.
            """
            if role not in role_class_pools:
                base_options = list(self.ROLE_TO_CLASSES.get(role, ["Guardian Firebrand"]))

                meta: list[str] = []
                try:
                    meta = self._get_meta_classes_for_role(role, request.mode or "wvw_zerg")
                except Exception:
                    meta = []

                ordered: list[str] = []
                seen: set[str] = set()

                for cls in meta:
                    if cls not in seen:
                        ordered.append(cls)
                        seen.add(cls)

                for cls in base_options:
                    if cls not in seen:
                        ordered.append(cls)
                        seen.add(cls)

                candidates = ordered or base_options
                role_class_pools[role] = candidates
                role_class_idx[role] = 0

            pool = role_class_pools[role]
            if not pool:
                return "Guardian Firebrand"

            idx = role_class_idx[role] % len(pool)
            role_class_idx[role] += 1
            return pool[idx]

        # Préparer tous les slots à optimiser (parallélisable)
        slot_specs = []
        for group_idx in range(request.groups):
            for slot_idx in range(slots_per_group):
                role_idx = slot_idx % len(request.roles_per_group)
                role = request.roles_per_group[role_idx]

                # Choisir la classe
                if slot_idx < len(constrained_classes):
                    class_spec = constrained_classes[slot_idx]
                    profession, spec = self._parse_class_spec(class_spec)
                else:
                    if is_small_roam:
                        class_spec = _next_class_for_role(role)
                    else:
                        class_spec = self._select_class_for_role(role, mode=request.mode)
                    profession, spec = self._parse_class_spec(class_spec)

                slot_specs.append((group_idx, role, profession, spec))
        
        # Optimiser TOUS les slots en parallèle (BOOST PERFORMANCE !)
        async def optimize_single_slot(spec_tuple):
            group_idx, role, profession, specialization = spec_tuple
            return (
                group_idx,
                await self._optimize_slot(
                    role=role,
                    profession=profession,
                    specialization=specialization,
                    experience=request.experience,
                    mode=request.mode,
                ),
            )
        
        async with async_timer("Build all slots"):
            optimized_slots = await batch_processor.batch_process(
                slot_specs,
                optimize_single_slot,
                show_progress=True
            )
        
        # Réorganiser par groupe
        groups: List[TeamGroup] = []
        for group_idx in range(request.groups):
            group_slots = [
                slot_build for g_idx, slot_build in optimized_slots
                if g_idx == group_idx and not isinstance(slot_build, Exception)
            ]
            groups.append(TeamGroup(index=group_idx + 1, slots=group_slots))
        
        # Analyser synergie
        synergy_score, synergy_details = self._analyze_synergy(groups, request)
        
        # Générer notes
        notes = self._generate_notes(groups, synergy_details)
        
        return TeamResult(
            groups=groups,
            synergy_score=synergy_score,
            synergy_details=synergy_details,
            notes=notes,
        )
    
    @async_timed
    async def _build_team_with_strategy(self, request: TeamRequest) -> TeamResult:
        """Construit l'équipe en délégant la composition à TeamStrategyAgent.

        Cette voie "AI-first" laisse le LLM décider des rôles, classes et
        spécialisations pour chaque slot, puis réutilise _optimize_slot pour
        équiper chaque joueur.
        """

        ts_request = TeamStrategyRequest(
            message=request.user_message,
            explicit_mode=request.mode,
            explicit_experience=request.experience,
            constraints=request.constraints or {},
        )

        plan: TeamStrategyPlan = await self.strategy_agent.propose_strategy(ts_request)

        if not plan.groups:
            raise ValueError("TeamStrategyPlan has no groups")

        groups: List[TeamGroup] = []

        for g in plan.groups:
            group_slots: List[SlotBuild] = []
            for s in g.slots:
                role_enum = self._map_strategy_role_to_role_enum(s.role)
                slot_build = await self._optimize_slot(
                    role=role_enum,
                    profession=s.profession,
                    specialization=s.specialization,
                    experience=request.experience,
                    mode=request.mode,
                    weapon_preference=getattr(s, "weapon_preference", None),
                )
                group_slots.append(slot_build)

            groups.append(TeamGroup(index=g.index, slots=group_slots))

        # Analyse synergie et notes basées sur le résultat effectif
        synergy_score, synergy_details = self._analyze_synergy(groups, request)
        notes = self._generate_notes(groups, synergy_details)

        return TeamResult(
            groups=groups,
            synergy_score=synergy_score,
            synergy_details=synergy_details,
            notes=notes,
        )

    def _map_strategy_role_to_role_enum(self, role_label: str) -> Role:
        """Mappe un label de rôle libre (LLM) vers l'enum interne Role."""

        r = (role_label or "").strip().lower()
        if not r:
            return Role.DPS

        if "stab" in r or "stability" in r:
            return Role.STAB
        if "heal" in r or "healer" in r or "soin" in r:
            return Role.HEAL
        if "boon" in r or "quick" in r or "alac" in r:
            return Role.BOON
        if "strip" in r or "corrupt" in r or "corruption" in r:
            return Role.STRIP
        if "tank" in r or "frontline" in r:
            return Role.TANK
        if "cleanse" in r or "clean" in r:
            return Role.CLEANSE
        if "support" in r:
            return Role.SUPPORT

        return Role.DPS

    @lru_cache(maxsize=128)
    def _parse_class_spec(self, class_spec: str) -> tuple[str, str]:
        """
        Parse "Guardian Firebrand" → ("Guardian", "Firebrand").
        
        OPTIMISÉ : Utilise lru_cache pour éviter de parser plusieurs fois.
        """
        if " " in class_spec:
            parts = class_spec.split()
            return parts[0], parts[1] if len(parts) > 1 else parts[0]
        else:
            # Spec seule donnée (ex: "Firebrand")
            # Deduire la profession
            spec_to_prof = {
                "Firebrand": "Guardian",
                "Willbender": "Guardian",
                "Druid": "Ranger",
                "Soulbeast": "Ranger",
                "Herald": "Revenant",
                "Renegade": "Revenant",
                "Spellbreaker": "Warrior",
                "Berserker": "Warrior",
                "Scrapper": "Engineer",
                "Holosmith": "Engineer",
                "Mechanist": "Engineer",
                "Reaper": "Necromancer",
                "Scourge": "Necromancer",
                "Harbinger": "Necromancer",
                "Deadeye": "Thief",
                "Daredevil": "Thief",
                "Specter": "Thief",
                "Chronomancer": "Mesmer",
                "Mirage": "Mesmer",
                "Virtuoso": "Mesmer",
                "Tempest": "Elementalist",
                "Weaver": "Elementalist",
                "Catalyst": "Elementalist",
            }
            profession = spec_to_prof.get(class_spec, class_spec)
            return profession, class_spec
    
    def _get_meta_classes_for_role(self, role: Role, game_mode: str) -> List[str]:
        """Retourne une liste de classes 'Profession Specialization' issues des builds méta."""

        if not hasattr(self, "meta_rag") or self.meta_rag is None:
            return []

        hits = self.meta_rag.retrieve_for_build(
            game_mode=game_mode or "wvw_zerg",
            profession=None,
            specialization=None,
            role=role.value,
            question=None,
            max_results=5,
        )

        classes: List[str] = []
        for h in hits:
            prof = h.get("profession")
            spec = h.get("specialization")
            if isinstance(prof, str) and isinstance(spec, str):
                classes.append(f"{prof} {spec}")
        return classes

    def _select_class_for_role(self, role: Role, mode: Optional[str] = None) -> str:
        """
        Sélectionne la meilleure classe pour un rôle donné.
        """
        options = list(self.ROLE_TO_CLASSES.get(role, ["Guardian Firebrand"]))

        meta_classes: List[str] = []
        if mode is not None:
            try:
                meta_classes = self._get_meta_classes_for_role(role, mode)
            except Exception as e:  # pragma: no cover - garde-fou
                logger.warning("MetaRAG in TeamCommander failed", extra={"error": str(e)})
                meta_classes = []

        if meta_classes:
            # Mettre en tête les classes issues des builds méta, puis les
            # options historiques, sans doublons.
            ordered: List[str] = []
            seen: set[str] = set()

            for cls in meta_classes:
                if cls not in seen:
                    ordered.append(cls)
                    seen.add(cls)

            for cls in options:
                if cls not in seen:
                    ordered.append(cls)
                    seen.add(cls)

            options = ordered

        # Prendre la première option (priorité aux builds méta, puis historique)
        return options[0]
    
    async def _optimize_slot(
        self,
        role: Role,
        profession: str,
        specialization: str,
        experience: str = "beginner",
        mode: str = "wvw_zerg",
        weapon_preference: Optional[str] = None,
    ) -> SlotBuild:
        """Optimise un slot individuel (runes, sigils, stats).

        Cette version V2 teste plusieurs presets de stats par rôle
        (ex: Berserker/Marauder pour DPS, Minstrel/Harrier/Cleric pour Heal)
        et laisse le moteur choisir la meilleure combinaison complète.
        """
        # Skill rotation simplifiée (placeholder)
        skill_rotation = [
            {"name": "Burst 1", "damage_coefficient": 2.0},
            {"name": "Burst 2", "damage_coefficient": 1.5},
            {"name": "Auto Attack", "damage_coefficient": 0.8},
        ]

        # Optimiser via BuildEquipmentOptimizer avec des rôles fins
        if role in [Role.DPS, Role.STRIP]:
            optimizer_role = "dps"
        elif role == Role.HEAL:
            optimizer_role = "heal"
        elif role == Role.BOON:
            optimizer_role = "boon"
        elif role in [Role.TANK, Role.STAB]:
            optimizer_role = "tank"
        else:
            optimizer_role = "support"

        # Construire les presets de stats en deux temps:
        #   1) utiliser le Greedy Gear Solver pour obtenir un mix d'armure
        #      pièce par pièce (base_stats mixées) ;
        #   2) ajouter les presets classiques "full prefix" comme candidats
        #      supplémentaires et fallback.

        stat_presets: List[tuple[str, Dict[str, int]]] = []

        # Mixer d'armure potentiel issu du greedy solver (slot -> prefix)
        greedy_armor_mix: Optional[Dict[str, str]] = None

        # 1) Greedy gear solver (armor mix)
        try:
            gear_result = self.gear_optimization_service.generate_equipment_set(
                role=optimizer_role,
                profession=profession,
                specialization=specialization,
                mode=mode,
                experience=experience,
            )
            stat_presets.append(("GreedyMix", gear_result.base_stats))
            greedy_armor_mix = dict(gear_result.equipment_set.armor or {})
        except Exception as e:
            logger.warning(
                "GearOptimizationService failed in TeamCommander; falling back to presets.",
                extra={"error": str(e)},
            )

        # 2) Presets classiques par préfixe (Berserker, Marauder, Minstrel, ...)
        try:
            preset_list = self._get_stat_presets_for_role(role, mode)
            stat_presets.extend(preset_list)
        except Exception as e:
            logger.error(
                "Failed to build stat presets for role in TeamCommander.",
                extra={"error": str(e)},
            )
        candidates: List[BuildCandidate] = []
        results_by_id: Dict[str, OptimizationResult] = {}

        # Construire des contraintes pour le moteur d'équipement
        base_constraints: Dict[str, Any] = {"mode": mode, "experience": experience}
        if weapon_preference:
            base_constraints["weapon_preference"] = weapon_preference

        for idx, (preset_name, base_stats) in enumerate(stat_presets):
            try:
                opt = await self.optimizer.optimize_build(
                    base_stats=base_stats,
                    skill_rotation=skill_rotation,
                    role=optimizer_role,
                    constraints=base_constraints,
                )
            except Exception as e:  # pragma: no cover - robust à l'échec isolé
                logger.error(f"Slot optimization failed for preset {preset_name}: {e}")
                continue

            candidate_id = f"{preset_name}-{idx}"
            results_by_id[candidate_id] = opt
            candidates.append(
                BuildCandidate(
                    id=candidate_id,
                    prefix=preset_name,
                    role=optimizer_role,
                    rune=opt.rune_name,
                    sigils=opt.sigil_names,
                    total_damage=opt.total_damage,
                    survivability=opt.survivability_score,
                    overall_score=opt.overall_score,
                )
            )

        best_result: OptimizationResult
        best_preset_name: str
        advisor_reason: Optional[str] = None
        advisor_alternatives: Optional[List[Dict[str, Any]]] = None

        if candidates:
            try:
                decision = await self.build_advisor.choose_best_candidate(
                    candidates=candidates,
                    role=optimizer_role,
                    context={"mode": mode, "experience": experience},
                )
                advised = decision.candidate
                advisor_reason = decision.reason
                ranked = decision.ranked_candidates or []
                # Construire une petite liste d'alternatives (hors meilleur)
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
                    if len(alts) >= 2:
                        break
                advisor_alternatives = alts or None
                best_result = results_by_id[advised.id]
                best_preset_name = advised.prefix
            except Exception as e:  # pragma: no cover - robust fallback
                logger.error(f"BuildAdvisorAgent failed, falling back to max score: {e}")
                # Fallback: max overall_score
                best_candidate = max(candidates, key=lambda c: c.overall_score)
                best_result = results_by_id[best_candidate.id]
                best_preset_name = best_candidate.prefix
        else:
            base_stats = self._get_base_stats_for_role(role)
            best_result = await self.optimizer.optimize_build(
                base_stats=base_stats,
                skill_rotation=skill_rotation,
                role=optimizer_role,
            )
            best_preset_name = self._get_stats_priority_for_role(role)

        stats_priority = best_preset_name or self._get_stats_priority_for_role(role)

        # Conserver le mix d'armure détaillé uniquement si le preset GreedyMix a été choisi.
        final_gear_mix: Optional[Dict[str, str]] = None
        if stats_priority == "GreedyMix" and greedy_armor_mix:
            final_gear_mix = greedy_armor_mix

        return SlotBuild(
            role=role,
            profession=profession,
            specialization=specialization,
            rune=best_result.rune_name,
            sigils=best_result.sigil_names,
            stats_priority=stats_priority,
            performance={
                "burst_damage": best_result.total_damage,
                "survivability": best_result.survivability_score,
                "dps_increase": best_result.dps_increase_percent,
            },
            advisor_reason=advisor_reason,
            advisor_alternatives=advisor_alternatives,
            relic=best_result.relic_name,
            gear_mix=final_gear_mix,
        )
    
    def _get_stat_presets_for_role(self, role: Role, mode: Optional[str] = None) -> List[tuple[str, Dict[str, int]]]:
        """Retourne plusieurs presets de stats réalistes par rôle.

        Ces presets approximatifs représentent différents splits de gear
        (par ex. full Berserker vs Marauder pour DPS, Minstrel vs Harrier
        pour Heal), sans modéliser chaque pièce individuellement.
        """
        m = (mode or "").lower() if isinstance(mode, str) else ""

        # Utiliser toutes les stats connues via itemstats.json pour découvrir
        # dynamiquement les presets adaptés à chaque rôle.
        all_prefixes = get_all_prefixes()

        def _is_dps(stats: Dict[str, int]) -> bool:
            power = stats.get("power", 0)
            precision = stats.get("precision", 0)
            condi = stats.get("condition_damage", 0)
            expertise = stats.get("expertise", 0)

            is_power_dps = power >= 800 and precision >= 800
            is_condi_dps = condi >= 800 and expertise >= 800

            return is_power_dps or is_condi_dps

        def _is_boon_heal(stats: Dict[str, int]) -> bool:
            return stats.get("healing_power", 0) >= 800 and stats.get("concentration", 0) >= 800

        def _is_heal_support(stats: Dict[str, int]) -> bool:
            return stats.get("healing_power", 0) >= 800 or stats.get("concentration", 0) >= 800

        def _is_boon(stats: Dict[str, int]) -> bool:
            return stats.get("concentration", 0) >= 800

        def _is_tank(stats: Dict[str, int]) -> bool:
            return stats.get("toughness", 0) >= 1200 and stats.get("vitality", 0) >= 1200

        names: List[str]

        if role in [Role.DPS, Role.STRIP]:
            # DPS: tous les préfixes avec beaucoup de power + precision
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_dps(stats)
            ]
            # Fallback statique si l'heuristique est trop stricte
            if not names:
                names = ["Berserker", "Marauder", "Dragon", "Valkyrie"]
        elif role in [Role.HEAL, Role.SUPPORT, Role.CLEANSE]:
            # Heal/support: focus sur healing_power et/ou concentration.
            candidates = [
                name
                for name, stats in all_prefixes.items()
                if _is_boon_heal(stats) or _is_heal_support(stats)
            ]
            if m == "wvw_roam":
                # En roaming, garder explicitement Celestial si présent.
                if "Celestial" in all_prefixes and "Celestial" not in candidates:
                    candidates.append("Celestial")
            if candidates:
                names = sorted(set(candidates))
            else:
                names = ["Minstrel", "Harrier", "Cleric", "Magi"]
        elif role == Role.BOON:
            # Boon share: forte concentration, avec ou sans heal.
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_boon(stats)
            ]
            if not names:
                names = ["Diviner", "Minstrel", "Harrier"]
        else:
            # Tank / stab: grosses valeurs de toughness + vitality.
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_tank(stats)
            ]
            if not names:
                names = ["Minstrel", "Soldier", "Trailblazer", "Dire"]

        filtered_names = filter_prefix_names_by_itemstats(names)
        return [(name, get_prefix_stats(name)) for name in filtered_names]

    def _get_base_stats_for_role(self, role: Role) -> Dict[str, int]:
        """Retourne des stats de base selon le rôle (fallback V1) via préfixes."""
        if role in [Role.DPS, Role.STRIP]:
            return get_prefix_stats("Berserker")
        if role in [Role.HEAL, Role.SUPPORT, Role.CLEANSE]:
            return get_prefix_stats("Minstrel")
        if role == Role.BOON:
            return get_prefix_stats("Diviner")
        return get_prefix_stats("Soldier")
    
    def _get_stats_priority_for_role(self, role: Role) -> str:
        """Retourne la stat priority (gear) selon le rôle."""
        mapping = {
            Role.DPS: "Berserker",
            Role.STRIP: "Berserker",
            Role.HEAL: "Minstrel",
            Role.SUPPORT: "Minstrel",
            Role.CLEANSE: "Cleric",
            Role.BOON: "Diviner",
            Role.STAB: "Minstrel",
            Role.TANK: "Soldier",
        }
        return mapping.get(role, "Berserker")
    
    def _analyze_synergy(
        self, groups: List[TeamGroup], request: TeamRequest
    ) -> tuple[str, Dict[str, str]]:
        """
        Analyse la synergie globale de la team.
        
        Returns:
            (score, details) où score in ["S", "A", "B", "C"]
        """
        role_counts = {role: 0 for role in Role}
        per_group_counts: List[Dict[Role, int]] = []

        for group in groups:
            group_counts = {role: 0 for role in Role}
            for slot in group.slots:
                role_counts[slot.role] += 1
                group_counts[slot.role] += 1
            per_group_counts.append(group_counts)

        details: Dict[str, str] = {}
        score_points = 0

        missing_stab_groups: List[str] = []
        weak_heal_groups: List[str] = []
        missing_boon_groups: List[str] = []
        missing_cleanse_groups: List[str] = []
        low_damage_groups: List[str] = []

        for idx, group_counts in enumerate(per_group_counts, start=1):
            if group_counts[Role.STAB] < 1:
                missing_stab_groups.append(str(idx))
            if group_counts[Role.HEAL] < 1 and group_counts[Role.SUPPORT] < 1:
                weak_heal_groups.append(str(idx))
            if group_counts[Role.BOON] < 1:
                missing_boon_groups.append(str(idx))
            if group_counts[Role.CLEANSE] < 1:
                missing_cleanse_groups.append(str(idx))
            if (group_counts[Role.DPS] + group_counts[Role.STRIP]) <= 1:
                low_damage_groups.append(str(idx))

        num_groups = len(per_group_counts) or 1

        if role_counts[Role.STAB] >= num_groups and not missing_stab_groups:
            details["stability"] = "Excellent"
            score_points += 3
        elif role_counts[Role.STAB] >= 1:
            details["stability"] = "Good"
            score_points += 2
        else:
            details["stability"] = "Weak"

        total_healers = role_counts[Role.HEAL] + role_counts[Role.SUPPORT]
        if total_healers >= num_groups and not weak_heal_groups:
            details["healing"] = "Optimal"
            score_points += 3
        elif total_healers >= 1:
            details["healing"] = "Good"
            score_points += 2
        else:
            details["healing"] = "Weak"

        boon_providers = role_counts[Role.BOON]
        if boon_providers >= num_groups and not missing_boon_groups:
            details["boon_share"] = "Perfect"
            score_points += 3
        elif boon_providers >= 1:
            details["boon_share"] = "Good"
            score_points += 2
        else:
            details["boon_share"] = "Weak"

        strip_providers = role_counts[Role.STRIP]
        if strip_providers >= num_groups:
            details["boon_strip"] = "Effective"
            score_points += 2
        elif strip_providers >= 1:
            details["boon_strip"] = "Moderate"
            score_points += 1
        else:
            details["boon_strip"] = "Weak"

        total_dps_like = role_counts[Role.DPS] + role_counts[Role.STRIP]
        if total_dps_like >= 2 * num_groups and not low_damage_groups:
            details["damage"] = "Very High"
            score_points += 3
        elif total_dps_like >= num_groups:
            details["damage"] = "High"
            score_points += 2
        else:
            details["damage"] = "Moderate"
            score_points += 1

        cleanse_providers = role_counts[Role.CLEANSE]
        if cleanse_providers >= num_groups and not missing_cleanse_groups:
            details["cleanse"] = "Excellent"
            score_points += 2
        elif cleanse_providers >= 1:
            details["cleanse"] = "Good"
            score_points += 1
        else:
            details["cleanse"] = "Weak"

        if missing_stab_groups:
            details["group_stability_issues"] = ",".join(missing_stab_groups)
        else:
            details["group_stability_issues"] = ""

        if weak_heal_groups:
            details["group_healing_issues"] = ",".join(weak_heal_groups)
        else:
            details["group_healing_issues"] = ""

        if missing_boon_groups:
            details["group_boon_issues"] = ",".join(missing_boon_groups)
        else:
            details["group_boon_issues"] = ""

        if missing_cleanse_groups:
            details["group_cleanse_issues"] = ",".join(missing_cleanse_groups)
        else:
            details["group_cleanse_issues"] = ""

        if low_damage_groups:
            details["group_damage_issues"] = ",".join(low_damage_groups)
        else:
            details["group_damage_issues"] = ""

        if score_points >= 14:
            score = "S"
        elif score_points >= 10:
            score = "A"
        elif score_points >= 6:
            score = "B"
        else:
            score = "C"

        return score, details
    
    def _generate_notes(
        self, groups: List[TeamGroup], synergy_details: Dict[str, str]
    ) -> List[str]:
        notes = []
        
        # Stabilité
        if synergy_details.get("stability") == "Excellent":
            notes.append("✅ Couverture Stabilité excellente")
        elif synergy_details.get("stability") == "Weak":
            notes.append("⚠️ Manque de Stabilité - Ajoutez un Firebrand ou Chronomancer")
        
        # Soins
        if synergy_details.get("healing") == "Optimal":
            notes.append("✅ Soins optimaux pour un groupe de cette taille")
        elif synergy_details.get("healing") == "Weak":
            notes.append("⚠️ Manque de soins - Ajoutez un Druid ou Scrapper")
        
        # Boon share
        if synergy_details.get("boon_share") == "Perfect":
            notes.append("✅ Might stacking parfait")
        elif synergy_details.get("boon_share") == "Weak":
            notes.append("⚠️ Manque de boon share - Ajoutez un Herald")
        
        # DPS
        if synergy_details.get("damage") == "Very High":
            notes.append("✅ Burst damage très élevé")
        
        # Cleanse
        if synergy_details.get("cleanse") == "Weak":
            notes.append("⚠️ Faible cleanse - Vulnérable aux condi")
        
        group_stab_issues = synergy_details.get("group_stability_issues") or ""
        if group_stab_issues:
            notes.append(f"⚠️ Groupes sans Stabilité dédiée: {group_stab_issues}")

        group_heal_issues = synergy_details.get("group_healing_issues") or ""
        if group_heal_issues:
            notes.append(f"⚠️ Groupes sous-dotés en soins/support: {group_heal_issues}")

        group_boon_issues = synergy_details.get("group_boon_issues") or ""
        if group_boon_issues:
            notes.append(f"⚠️ Groupes sans booner dédié: {group_boon_issues}")

        group_cleanse_issues = synergy_details.get("group_cleanse_issues") or ""
        if group_cleanse_issues:
            notes.append(f"⚠️ Groupes sans cleanse dédié: {group_cleanse_issues}")

        group_damage_issues = synergy_details.get("group_damage_issues") or ""
        if group_damage_issues:
            notes.append(f"⚠️ Groupes avec DPS/strip insuffisant: {group_damage_issues}")
        
        return notes


# Instance globale
_team_commander = None


def get_team_commander() -> TeamCommanderAgent:
    """Get or create the global TeamCommanderAgent instance."""
    global _team_commander
    if _team_commander is None:
        _team_commander = TeamCommanderAgent()
    return _team_commander
