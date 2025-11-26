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
from app.engine.gear.prefixes import get_prefix_stats
from app.agents.build_advisor_agent import BuildAdvisorAgent, BuildCandidate
from app.services.gear_prefix_validator import filter_prefix_names_by_itemstats


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
    
    def __init__(self):
        self.optimizer = get_build_optimizer()
        self.build_advisor = BuildAdvisorAgent()
    
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
            groups = team_size // 5  # Assume groupes de 5
        
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
        
        # Si aucun rôle détecté, utiliser composition standard
        if not roles:
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
        
        return TeamRequest(
            team_size=team_size,
            groups=groups,
            roles_per_group=roles,
            constraints=constraints,
            user_message=message,
            experience="beginner",
            mode="wvw_zerg",
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
                    class_spec = self._select_class_for_role(role)
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
    
    def _select_class_for_role(self, role: Role) -> str:
        """
        Sélectionne la meilleure classe pour un rôle donné.
        """
        options = self.ROLE_TO_CLASSES.get(role, ["Guardian Firebrand"])
        # Prendre la première option (meta)
        return options[0]
    
    async def _optimize_slot(
        self,
        role: Role,
        profession: str,
        specialization: str,
        experience: str = "beginner",
        mode: str = "wvw_zerg",
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

        stat_presets = self._get_stat_presets_for_role(role)
        candidates: List[BuildCandidate] = []
        results_by_id: Dict[str, OptimizationResult] = {}

        for idx, (preset_name, base_stats) in enumerate(stat_presets):
            try:
                opt = await self.optimizer.optimize_build(
                    base_stats=base_stats,
                    skill_rotation=skill_rotation,
                    role=optimizer_role,
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
                decision = self.build_advisor.choose_best_candidate(
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
        )
    
    def _get_stat_presets_for_role(self, role: Role) -> List[tuple[str, Dict[str, int]]]:
        """Retourne plusieurs presets de stats réalistes par rôle.

        Ces presets approximatifs représentent différents splits de gear
        (par ex. full Berserker vs Marauder pour DPS, Minstrel vs Harrier
        pour Heal), sans modéliser chaque pièce individuellement.
        """
        if role in [Role.DPS, Role.STRIP]:
            # DPS: presets classiques + une option plus tanky (Valkyrie)
            names = ["Berserker", "Marauder", "Dragon", "Valkyrie"]
        elif role in [Role.HEAL, Role.SUPPORT, Role.CLEANSE]:
            names = ["Minstrel", "Harrier", "Cleric", "Magi"]
        elif role == Role.BOON:
            names = ["Diviner", "Minstrel", "Harrier"]
        else:
            # Tank / fallback support: ajouter quelques variantes plus off-meta (Trailblazer/Dire)
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
        # Compter les rôles
        role_counts = {role: 0 for role in Role}
        for group in groups:
            for slot in group.slots:
                role_counts[slot.role] += 1
        
        details = {}
        score_points = 0
        
        # Stabilité
        if role_counts[Role.STAB] >= 2:
            details["stability"] = "Excellent"
            score_points += 3
        elif role_counts[Role.STAB] >= 1:
            details["stability"] = "Good"
            score_points += 2
        else:
            details["stability"] = "Weak"
            score_points += 0
        
        # Soins
        if role_counts[Role.HEAL] >= 2:
            details["healing"] = "Optimal"
            score_points += 3
        elif role_counts[Role.HEAL] >= 1:
            details["healing"] = "Good"
            score_points += 2
        else:
            details["healing"] = "Weak"
            score_points += 0
        
        # Boon share
        if role_counts[Role.BOON] >= 2:
            details["boon_share"] = "Perfect"
            score_points += 3
        elif role_counts[Role.BOON] >= 1:
            details["boon_share"] = "Good"
            score_points += 2
        else:
            details["boon_share"] = "Weak"
            score_points += 0
        
        # Strip
        if role_counts[Role.STRIP] >= 2:
            details["boon_strip"] = "Effective"
            score_points += 2
        elif role_counts[Role.STRIP] >= 1:
            details["boon_strip"] = "Moderate"
            score_points += 1
        else:
            details["boon_strip"] = "Weak"
            score_points += 0
        
        # DPS
        if role_counts[Role.DPS] >= 3:
            details["damage"] = "Very High"
            score_points += 3
        elif role_counts[Role.DPS] >= 2:
            details["damage"] = "High"
            score_points += 2
        else:
            details["damage"] = "Moderate"
            score_points += 1
        
        # Cleanse
        if role_counts[Role.CLEANSE] >= 2:
            details["cleanse"] = "Excellent"
            score_points += 2
        elif role_counts[Role.CLEANSE] >= 1:
            details["cleanse"] = "Good"
            score_points += 1
        else:
            details["cleanse"] = "Weak"
            score_points += 0
        
        # Score final
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
        """
        Génère des notes et recommandations pour la team.
        """
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
        
        return notes


# Instance globale
_team_commander = None


def get_team_commander() -> TeamCommanderAgent:
    """Get or create the global TeamCommanderAgent instance."""
    global _team_commander
    if _team_commander is None:
        _team_commander = TeamCommanderAgent()
    return _team_commander
