"""
GW2 Data Service - Intelligence Layer for GW2 Data

Service unifié qui combine :
- L'API officielle GW2 (via GW2APIClient)
- Le store local (via GW2DataStore)
- Le cache Redis pour les données fréquemment utilisées
- Des helpers intelligents pour la détection de rôle et le meta_context

Ce service est la brique fondamentale pour rendre l'IA plus intelligente
en lui fournissant un contexte riche et précis sur les builds GW2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import logger
from app.services.gw2_api_client import GW2APIClient
from app.services.gw2_data_store import GW2DataStore
from app.services.meta_build_catalog import (
    MetaBuild,
    find_closest_meta_build,
    query_meta_builds,
    load_meta_builds_from_json,
    META_BUILD_REGISTRY,
)


# ============================================================================
# Role Detection Constants
# ============================================================================

HEAL_KEYWORDS = frozenset([
    "heal", "healing", "regeneration", "regen", "restore", "restoration",
    "soin", "soigne", "régénération", "life", "health", "vigor",
    "rejuvenation", "renew", "mend", "recovery",
])

SUPPORT_KEYWORDS = frozenset([
    "support", "boon", "stability", "aegis", "protection", "resistance",
    "quickness", "alacrity", "might", "fury", "swiftness", "vigor",
    "resolution", "barrier", "aegis", "cleanse", "condi cleanse",
    "condition removal", "stunbreak", "stun break",
])

TANK_KEYWORDS = frozenset([
    "tank", "toughness", "vitality", "endurance", "defense", "defensive",
    "block", "invuln", "invulnerable", "evade", "dodge", "aegis",
    "protection", "barrier", "sustain", "survivability",
])

DPS_KEYWORDS = frozenset([
    "dps", "damage", "power", "burst", "strike", "critical", "crit",
    "ferocity", "precision", "attack", "offensive", "spike",
])

CONDI_DPS_KEYWORDS = frozenset([
    "condition", "condi", "bleed", "bleeding", "burn", "burning",
    "poison", "torment", "confusion", "expertise", "condition damage",
])

BOON_KEYWORDS = frozenset([
    "boon", "might", "fury", "quickness", "alacrity", "swiftness",
    "vigor", "regeneration", "protection", "resistance", "stability",
    "aegis", "resolution",
])

# Elite specialization -> primary role mapping
ELITE_SPEC_ROLES: Dict[str, str] = {
    # Guardian
    "Firebrand": "support",
    "Dragonhunter": "dps",
    "Willbender": "dps",
    
    # Warrior
    "Berserker": "dps",
    "Spellbreaker": "support",
    "Bladesworn": "dps",
    
    # Revenant
    "Herald": "support",
    "Renegade": "support",
    "Vindicator": "dps",
    
    # Engineer
    "Scrapper": "support",
    "Holosmith": "dps",
    "Mechanist": "support",
    
    # Ranger
    "Druid": "support",
    "Soulbeast": "dps",
    "Untamed": "dps",
    
    # Thief
    "Daredevil": "dps",
    "Deadeye": "dps",
    "Specter": "support",
    
    # Elementalist
    "Tempest": "support",
    "Weaver": "dps",
    "Catalyst": "dps",
    
    # Mesmer
    "Chronomancer": "support",
    "Mirage": "dps",
    "Virtuoso": "dps",
    
    # Necromancer
    "Reaper": "dps",
    "Scourge": "support",
    "Harbinger": "dps",
}

# Game mode specific role adjustments
WVW_SUPPORT_SPECS = frozenset([
    "Firebrand", "Scrapper", "Tempest", "Herald", "Scourge",
    "Spellbreaker", "Chronomancer", "Druid",
])

WVW_DPS_SPECS = frozenset([
    "Reaper", "Harbinger", "Willbender", "Dragonhunter",
    "Berserker", "Soulbeast", "Deadeye", "Weaver", "Virtuoso",
])


@dataclass
class RoleAnalysis:
    """Result of role detection from build data."""
    
    primary_role: str  # heal, support, tank, dps, condi_dps
    confidence: float  # 0.0 - 1.0
    secondary_roles: List[str] = field(default_factory=list)
    signals: Dict[str, List[str]] = field(default_factory=dict)  # role -> list of evidence


@dataclass
class MetaContext:
    """Rich context about the current meta for AnalystAgent."""
    
    current_meta_builds: List[Dict[str, Any]]
    role_distribution: Dict[str, int]
    popular_specs: List[str]
    closest_meta_build: Optional[MetaBuild]
    meta_diff: Optional[Dict[str, Any]]  # Differences between user build and closest meta
    summary: str


class Gw2DataService:
    """
    Service unifié pour l'accès intelligent aux données GW2.
    
    Combine l'API officielle, le store local et le meta_build_catalog
    pour fournir un contexte riche à l'IA.
    """
    
    def __init__(
        self,
        api_client: Optional[GW2APIClient] = None,
        data_store: Optional[GW2DataStore] = None,
        meta_builds_path: Optional[Path] = None,
    ) -> None:
        self.api_client = api_client or GW2APIClient()
        self.data_store = data_store or GW2DataStore()
        
        # Load meta builds if path provided
        if meta_builds_path and meta_builds_path.exists():
            count = load_meta_builds_from_json(meta_builds_path)
            logger.info(f"Gw2DataService: loaded {count} meta builds from {meta_builds_path}")
        
        # Index caches for fast lookup
        self._spec_by_id: Dict[int, Dict[str, Any]] = {}
        self._spec_by_name: Dict[str, Dict[str, Any]] = {}
        self._trait_by_id: Dict[int, Dict[str, Any]] = {}
        self._skill_by_id: Dict[int, Dict[str, Any]] = {}
        self._profession_by_name: Dict[str, Dict[str, Any]] = {}
        
        self._indexes_built = False
    
    def _build_indexes(self) -> None:
        """Build lookup indexes from local data store."""
        if self._indexes_built:
            return
        
        # Index specializations
        for spec in self.data_store.get_specializations():
            spec_id = spec.get("id")
            spec_name = spec.get("name", "")
            if spec_id:
                self._spec_by_id[spec_id] = spec
            if spec_name:
                self._spec_by_name[spec_name.lower()] = spec
        
        # Index traits
        for trait in self.data_store.get_traits():
            trait_id = trait.get("id")
            if trait_id:
                self._trait_by_id[trait_id] = trait
        
        # Index skills
        for skill in self.data_store.get_skills():
            skill_id = skill.get("id")
            if skill_id:
                self._skill_by_id[skill_id] = skill
        
        # Index professions
        for prof in self.data_store.get_professions():
            prof_name = prof.get("name", "")
            if prof_name:
                self._profession_by_name[prof_name.lower()] = prof
        
        self._indexes_built = True
        logger.info(
            f"Gw2DataService: built indexes - {len(self._spec_by_id)} specs, "
            f"{len(self._trait_by_id)} traits, {len(self._skill_by_id)} skills, "
            f"{len(self._profession_by_name)} professions"
        )
    
    # ========================================================================
    # Data Access Methods
    # ========================================================================
    
    def get_specialization(self, spec_id: int) -> Optional[Dict[str, Any]]:
        """Get specialization by ID from local store or API."""
        self._build_indexes()
        return self._spec_by_id.get(spec_id)
    
    def get_specialization_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specialization by name (case-insensitive)."""
        self._build_indexes()
        return self._spec_by_name.get(name.lower())
    
    def get_trait(self, trait_id: int) -> Optional[Dict[str, Any]]:
        """Get trait by ID from local store."""
        self._build_indexes()
        return self._trait_by_id.get(trait_id)
    
    def get_traits(self, trait_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple traits by IDs."""
        self._build_indexes()
        return [self._trait_by_id[tid] for tid in trait_ids if tid in self._trait_by_id]
    
    def get_skill(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """Get skill by ID from local store."""
        self._build_indexes()
        return self._skill_by_id.get(skill_id)
    
    def get_skills(self, skill_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple skills by IDs."""
        self._build_indexes()
        return [self._skill_by_id[sid] for sid in skill_ids if sid in self._skill_by_id]
    
    def get_profession(self, name: str) -> Optional[Dict[str, Any]]:
        """Get profession by name (case-insensitive)."""
        self._build_indexes()
        return self._profession_by_name.get(name.lower())
    
    # ========================================================================
    # Role Detection Intelligence
    # ========================================================================
    
    def _extract_text_signals(self, obj: Dict[str, Any]) -> str:
        """Extract searchable text from a GW2 object."""
        parts = []
        for key in ("name", "description"):
            val = obj.get(key)
            if isinstance(val, str):
                parts.append(val.lower())
        
        # Also check facts
        facts = obj.get("facts", [])
        if isinstance(facts, list):
            for f in facts:
                if isinstance(f, dict):
                    text = f.get("text", "")
                    if isinstance(text, str):
                        parts.append(text.lower())
        
        return " ".join(parts)
    
    def _count_keyword_matches(self, text: str, keywords: frozenset) -> int:
        """Count how many keywords appear in text."""
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        return count
    
    def detect_role(
        self,
        spec_id: Optional[int] = None,
        trait_ids: Optional[List[int]] = None,
        skill_ids: Optional[List[int]] = None,
        context: str = "",
    ) -> RoleAnalysis:
        """
        Detect the primary role of a build based on GW2 data.
        
        Uses multiple signals:
        - Elite specialization default role
        - Trait keywords and effects
        - Skill keywords and effects
        - Context string (e.g., "WvW Zerg heal Firebrand")
        """
        self._build_indexes()
        
        signals: Dict[str, List[str]] = {
            "heal": [],
            "support": [],
            "tank": [],
            "dps": [],
            "condi_dps": [],
            "boon": [],
        }
        
        scores: Dict[str, float] = {
            "heal": 0.0,
            "support": 0.0,
            "tank": 0.0,
            "dps": 0.0,
            "condi_dps": 0.0,
        }
        
        # 1. Check specialization
        spec_data = None
        spec_name = ""
        if spec_id:
            spec_data = self.get_specialization(spec_id)
            if spec_data:
                spec_name = spec_data.get("name", "")
                is_elite = spec_data.get("elite", False)
                
                if is_elite and spec_name in ELITE_SPEC_ROLES:
                    default_role = ELITE_SPEC_ROLES[spec_name]
                    scores[default_role] += 3.0
                    signals[default_role].append(f"Elite spec {spec_name} default role")
                
                # Check spec text
                spec_text = self._extract_text_signals(spec_data)
                for role, keywords in [
                    ("heal", HEAL_KEYWORDS),
                    ("support", SUPPORT_KEYWORDS),
                    ("tank", TANK_KEYWORDS),
                    ("dps", DPS_KEYWORDS),
                    ("condi_dps", CONDI_DPS_KEYWORDS),
                ]:
                    matches = self._count_keyword_matches(spec_text, keywords)
                    if matches > 0:
                        scores[role] += matches * 0.5
                        signals[role].append(f"Spec keywords: {matches} matches")
        
        # 2. Check traits
        if trait_ids:
            traits = self.get_traits(trait_ids)
            for trait in traits:
                trait_text = self._extract_text_signals(trait)
                trait_name = trait.get("name", "unknown")
                
                for role, keywords in [
                    ("heal", HEAL_KEYWORDS),
                    ("support", SUPPORT_KEYWORDS),
                    ("tank", TANK_KEYWORDS),
                    ("dps", DPS_KEYWORDS),
                    ("condi_dps", CONDI_DPS_KEYWORDS),
                ]:
                    matches = self._count_keyword_matches(trait_text, keywords)
                    if matches > 0:
                        scores[role] += matches * 0.3
                        signals[role].append(f"Trait '{trait_name}': {matches} {role} keywords")
        
        # 3. Check skills
        if skill_ids:
            skills = self.get_skills(skill_ids)
            for skill in skills:
                skill_text = self._extract_text_signals(skill)
                skill_name = skill.get("name", "unknown")
                
                for role, keywords in [
                    ("heal", HEAL_KEYWORDS),
                    ("support", SUPPORT_KEYWORDS),
                    ("tank", TANK_KEYWORDS),
                    ("dps", DPS_KEYWORDS),
                    ("condi_dps", CONDI_DPS_KEYWORDS),
                ]:
                    matches = self._count_keyword_matches(skill_text, keywords)
                    if matches > 0:
                        scores[role] += matches * 0.4
                        signals[role].append(f"Skill '{skill_name}': {matches} {role} keywords")
        
        # 4. Check context string
        ctx_lower = context.lower()
        for role, keywords in [
            ("heal", HEAL_KEYWORDS),
            ("support", SUPPORT_KEYWORDS),
            ("tank", TANK_KEYWORDS),
            ("dps", DPS_KEYWORDS),
            ("condi_dps", CONDI_DPS_KEYWORDS),
        ]:
            matches = self._count_keyword_matches(ctx_lower, keywords)
            if matches > 0:
                scores[role] += matches * 1.0  # Context is strong signal
                signals[role].append(f"Context keywords: {matches} matches")
        
        # 5. WvW-specific adjustments
        if "wvw" in ctx_lower or "zerg" in ctx_lower:
            if spec_name in WVW_SUPPORT_SPECS:
                scores["support"] += 1.5
                signals["support"].append(f"{spec_name} is WvW support meta")
            if spec_name in WVW_DPS_SPECS:
                scores["dps"] += 1.5
                signals["dps"].append(f"{spec_name} is WvW DPS meta")
        
        # Determine primary role
        if not any(scores.values()):
            return RoleAnalysis(
                primary_role="dps",
                confidence=0.3,
                secondary_roles=[],
                signals=signals,
            )
        
        sorted_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_role = sorted_roles[0][0]
        primary_score = sorted_roles[0][1]
        
        # Calculate confidence
        total_score = sum(scores.values())
        confidence = min(primary_score / max(total_score, 1.0), 1.0)
        
        # Determine secondary roles (at least 30% of primary score)
        threshold = primary_score * 0.3
        secondary_roles = [
            role for role, score in sorted_roles[1:]
            if score >= threshold
        ]
        
        return RoleAnalysis(
            primary_role=primary_role,
            confidence=confidence,
            secondary_roles=secondary_roles,
            signals=signals,
        )
    
    # ========================================================================
    # Meta Context Generation
    # ========================================================================
    
    def generate_meta_context(
        self,
        game_mode: str = "wvw",
        profession: Optional[str] = None,
        specialization: Optional[str] = None,
        role: Optional[str] = None,
        user_build_data: Optional[Dict[str, Any]] = None,
    ) -> MetaContext:
        """
        Generate a rich meta context for the AnalystAgent.
        
        This provides the AI with information about the current meta,
        popular builds, and how the user's build compares.
        """
        # Query relevant meta builds
        meta_builds = query_meta_builds(
            profession=profession,
            specialization=specialization,
            role=role,
            game_mode=game_mode,
        )
        
        # If no specific matches, get all for game mode
        if not meta_builds:
            meta_builds = query_meta_builds(game_mode=game_mode)
        
        # Build role distribution
        role_distribution: Dict[str, int] = {}
        popular_specs: List[str] = []
        seen_specs: Set[str] = set()
        
        for mb in meta_builds:
            role_distribution[mb.role] = role_distribution.get(mb.role, 0) + 1
            if mb.specialization not in seen_specs:
                popular_specs.append(mb.specialization)
                seen_specs.add(mb.specialization)
        
        # Find closest meta build to user's build
        closest_meta = find_closest_meta_build(
            profession=profession,
            specialization=specialization,
            role=role,
            game_mode=game_mode,
        )
        
        # Calculate diff if we have user build data and a closest meta
        meta_diff = None
        if closest_meta and user_build_data:
            meta_diff = self._calculate_meta_diff(user_build_data, closest_meta)
        
        # Generate summary
        summary_parts = []
        if meta_builds:
            summary_parts.append(f"{len(meta_builds)} meta builds found for {game_mode}")
        if role_distribution:
            roles_str = ", ".join(f"{r}: {c}" for r, c in sorted(role_distribution.items()))
            summary_parts.append(f"Role distribution: {roles_str}")
        if popular_specs[:5]:
            summary_parts.append(f"Popular specs: {', '.join(popular_specs[:5])}")
        if closest_meta:
            summary_parts.append(f"Closest meta: {closest_meta.name} ({closest_meta.specialization} {closest_meta.role})")
        
        summary = ". ".join(summary_parts) if summary_parts else "No meta context available"
        
        # Convert meta builds to dicts for JSON serialization
        meta_builds_data = [
            {
                "id": mb.id,
                "name": mb.name,
                "profession": mb.profession,
                "specialization": mb.specialization,
                "role": mb.role,
                "tags": mb.tags,
                "stats_text": mb.stats_text,
                "runes_text": mb.runes_text,
            }
            for mb in meta_builds[:10]  # Limit to top 10
        ]
        
        return MetaContext(
            current_meta_builds=meta_builds_data,
            role_distribution=role_distribution,
            popular_specs=popular_specs[:10],
            closest_meta_build=closest_meta,
            meta_diff=meta_diff,
            summary=summary,
        )
    
    def _calculate_meta_diff(
        self,
        user_build: Dict[str, Any],
        meta_build: MetaBuild,
    ) -> Dict[str, Any]:
        """
        Calculate differences between user build and a meta build.
        
        Returns a dict with:
        - equipment_diff: differences in stats/runes/sigils
        - missing_traits: traits in meta not in user build
        - extra_traits: traits in user not in meta
        """
        diff: Dict[str, Any] = {
            "meta_build_name": meta_build.name,
            "meta_build_id": meta_build.id,
        }
        
        # Compare equipment summary if available
        user_equipment = user_build.get("equipment_summary", {})
        if isinstance(user_equipment, dict):
            equipment_diff = {}
            
            if meta_build.stats_text:
                user_stats = user_equipment.get("stats_text", "")
                if user_stats and user_stats.lower() != meta_build.stats_text.lower():
                    equipment_diff["stats"] = {
                        "user": user_stats,
                        "meta": meta_build.stats_text,
                    }
            
            if meta_build.runes_text:
                user_runes = user_equipment.get("runes_text", "")
                if user_runes and user_runes.lower() != meta_build.runes_text.lower():
                    equipment_diff["runes"] = {
                        "user": user_runes,
                        "meta": meta_build.runes_text,
                    }
            
            if equipment_diff:
                diff["equipment_diff"] = equipment_diff
        
        return diff
    
    def compare_build_to_meta(
        self,
        spec_id: Optional[int] = None,
        trait_ids: Optional[List[int]] = None,
        skill_ids: Optional[List[int]] = None,
        gear_optimization: Optional[Dict[str, Any]] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Compare a user's build to the closest meta build and provide recommendations.
        
        Returns:
        - closest_meta: The meta build that best matches
        - similarity_score: 0.0 - 1.0 indicating how close the build is
        - recommendations: List of specific improvements
        - equipment_comparison: Detailed equipment diff
        """
        self._build_indexes()
        
        # Get user build info
        profession = None
        spec_name = None
        if spec_id:
            spec_data = self.get_specialization(spec_id)
            if spec_data:
                profession = spec_data.get("profession")
                spec_name = spec_data.get("name")
        
        # Detect role
        role_analysis = self.detect_role(
            spec_id=spec_id,
            trait_ids=trait_ids or [],
            skill_ids=skill_ids or [],
            context=context,
        )
        
        # Find closest meta build
        closest_meta = find_closest_meta_build(
            profession=profession,
            specialization=spec_name,
            role=role_analysis.primary_role,
            game_mode="wvw",
        )
        
        if not closest_meta:
            return {
                "closest_meta": None,
                "similarity_score": 0.0,
                "recommendations": ["No matching meta build found for this configuration"],
                "equipment_comparison": None,
            }
        
        # Calculate similarity score
        similarity_score = self._calculate_meta_similarity(
            spec_name=spec_name,
            role=role_analysis.primary_role,
            gear_optimization=gear_optimization,
            meta_build=closest_meta,
        )
        
        # Generate recommendations
        recommendations = self._generate_meta_recommendations(
            spec_name=spec_name,
            role=role_analysis.primary_role,
            gear_optimization=gear_optimization,
            meta_build=closest_meta,
            similarity_score=similarity_score,
        )
        
        # Equipment comparison
        equipment_comparison = None
        if gear_optimization:
            equipment_comparison = self._compare_equipment(gear_optimization, closest_meta)
        
        return {
            "closest_meta": {
                "id": closest_meta.id,
                "name": closest_meta.name,
                "profession": closest_meta.profession,
                "specialization": closest_meta.specialization,
                "role": closest_meta.role,
                "stats_text": closest_meta.stats_text,
                "runes_text": closest_meta.runes_text,
                "source": closest_meta.source,
                "notes": closest_meta.notes,
            },
            "similarity_score": similarity_score,
            "recommendations": recommendations,
            "equipment_comparison": equipment_comparison,
            "user_role": role_analysis.primary_role,
            "role_confidence": role_analysis.confidence,
        }
    
    def _calculate_meta_similarity(
        self,
        spec_name: Optional[str],
        role: str,
        gear_optimization: Optional[Dict[str, Any]],
        meta_build: MetaBuild,
    ) -> float:
        """Calculate similarity score between user build and meta build."""
        score = 0.0
        max_score = 0.0
        
        # Specialization match (30 points)
        max_score += 30.0
        if spec_name and spec_name.lower() == meta_build.specialization.lower():
            score += 30.0
        
        # Role match (20 points)
        max_score += 20.0
        if role.lower() == meta_build.role.lower():
            score += 20.0
        elif role in ("support", "heal", "boon") and meta_build.role in ("support", "heal", "boon"):
            score += 15.0  # Partial match for support variants
        
        # Equipment match (50 points)
        if gear_optimization:
            chosen = gear_optimization.get("chosen", {})
            
            # Stats prefix (20 points)
            max_score += 20.0
            user_prefix = chosen.get("prefix", "").lower()
            meta_prefix = (meta_build.stats_text or "").lower()
            if user_prefix and meta_prefix and user_prefix in meta_prefix:
                score += 20.0
            elif user_prefix and meta_prefix:
                # Partial match for similar prefixes
                similar_prefixes = {
                    "minstrel": ["harrier", "cleric"],
                    "harrier": ["minstrel", "cleric"],
                    "berserker": ["marauder", "dragon"],
                    "marauder": ["berserker", "valkyrie"],
                }
                if user_prefix in similar_prefixes.get(meta_prefix, []):
                    score += 10.0
            
            # Rune (15 points)
            max_score += 15.0
            user_rune = chosen.get("rune", "").lower()
            meta_rune = (meta_build.runes_text or "").lower()
            if user_rune and meta_rune and user_rune in meta_rune:
                score += 15.0
            
            # Relic (15 points) - if meta specifies one
            max_score += 15.0
            user_relic = chosen.get("relic", "").lower()
            if user_relic:
                score += 7.5  # Give half points if user has a relic
        else:
            max_score += 50.0  # Still count equipment in max even if not provided
        
        return min(score / max_score, 1.0) if max_score > 0 else 0.0
    
    def _generate_meta_recommendations(
        self,
        spec_name: Optional[str],
        role: str,
        gear_optimization: Optional[Dict[str, Any]],
        meta_build: MetaBuild,
        similarity_score: float,
    ) -> List[str]:
        """Generate specific recommendations to align with meta."""
        recommendations: List[str] = []
        
        # High similarity - already good
        if similarity_score >= 0.9:
            recommendations.append(f"Your build closely matches the meta {meta_build.name}. Well done!")
            return recommendations
        
        # Check specialization
        if spec_name and spec_name.lower() != meta_build.specialization.lower():
            recommendations.append(
                f"Consider using {meta_build.specialization} instead of {spec_name} "
                f"for optimal {meta_build.role} performance in WvW."
            )
        
        # Check equipment
        if gear_optimization:
            chosen = gear_optimization.get("chosen", {})
            
            # Stats
            user_prefix = chosen.get("prefix", "")
            meta_prefix = meta_build.stats_text or ""
            if user_prefix and meta_prefix and user_prefix.lower() not in meta_prefix.lower():
                recommendations.append(
                    f"Switch from {user_prefix} to {meta_prefix} stats for better {role} performance."
                )
            
            # Rune
            user_rune = chosen.get("rune", "")
            meta_rune = meta_build.runes_text or ""
            if user_rune and meta_rune and user_rune.lower() not in meta_rune.lower():
                recommendations.append(
                    f"Use {meta_rune} instead of {user_rune} for this build."
                )
        
        # General advice based on role
        if not recommendations:
            if role in ("support", "heal"):
                recommendations.append(
                    f"Check {meta_build.source or 'community guides'} for optimal trait selection for {meta_build.name}."
                )
            else:
                recommendations.append(
                    f"Refer to {meta_build.source or 'community guides'} for the current {meta_build.name} meta setup."
                )
        
        return recommendations
    
    def _compare_equipment(
        self,
        gear_optimization: Dict[str, Any],
        meta_build: MetaBuild,
    ) -> Dict[str, Any]:
        """Compare optimized equipment with meta build equipment."""
        chosen = gear_optimization.get("chosen", {})
        
        comparison = {
            "user_stats": chosen.get("prefix"),
            "meta_stats": meta_build.stats_text,
            "stats_match": False,
            "user_rune": chosen.get("rune"),
            "meta_rune": meta_build.runes_text,
            "rune_match": False,
            "user_sigils": chosen.get("sigils", []),
            "user_relic": chosen.get("relic"),
        }
        
        # Check matches
        if comparison["user_stats"] and comparison["meta_stats"]:
            comparison["stats_match"] = (
                comparison["user_stats"].lower() in comparison["meta_stats"].lower()
            )
        
        if comparison["user_rune"] and comparison["meta_rune"]:
            comparison["rune_match"] = (
                comparison["user_rune"].lower() in comparison["meta_rune"].lower()
            )
        
        return comparison
    
    def get_meta_context_string(
        self,
        game_mode: str = "wvw",
        profession: Optional[str] = None,
        specialization: Optional[str] = None,
        role: Optional[str] = None,
        user_build_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a formatted meta context string for the AnalystAgent prompt.
        """
        ctx = self.generate_meta_context(
            game_mode=game_mode,
            profession=profession,
            specialization=specialization,
            role=role,
            user_build_data=user_build_data,
        )
        
        parts = [ctx.summary]
        
        if ctx.meta_diff:
            diff_str = json.dumps(ctx.meta_diff, ensure_ascii=False)
            parts.append(f"Differences from closest meta: {diff_str}")
        
        if ctx.current_meta_builds:
            builds_preview = [
                f"- {b['name']} ({b['specialization']} {b['role']})"
                for b in ctx.current_meta_builds[:5]
            ]
            parts.append("Top meta builds:\n" + "\n".join(builds_preview))
        
        return "\n".join(parts)
    
    # ========================================================================
    # Profession/Spec Utilities
    # ========================================================================
    
    def get_profession_for_spec(self, spec_id: int) -> Optional[str]:
        """Get the profession name for a given specialization ID."""
        spec = self.get_specialization(spec_id)
        if not spec:
            return None
        return spec.get("profession")
    
    def is_elite_spec(self, spec_id: int) -> bool:
        """Check if a specialization is an elite spec."""
        spec = self.get_specialization(spec_id)
        if not spec:
            return False
        return spec.get("elite", False)
    
    def get_spec_name(self, spec_id: int) -> Optional[str]:
        """Get the name of a specialization by ID."""
        spec = self.get_specialization(spec_id)
        if not spec:
            return None
        return spec.get("name")


# Singleton instance for easy access
_gw2_data_service: Optional[Gw2DataService] = None


def get_gw2_data_service() -> Gw2DataService:
    """Get the singleton Gw2DataService instance."""
    global _gw2_data_service
    if _gw2_data_service is None:
        # Try to load meta builds from default location
        base_dir = Path(__file__).resolve().parents[2]
        meta_path = base_dir / "data" / "meta_builds_wvw.json"
        _gw2_data_service = Gw2DataService(meta_builds_path=meta_path)
    return _gw2_data_service
