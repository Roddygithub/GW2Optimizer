"""
Build Equipment Optimizer Agent - WvW ONLY

Cet agent utilise le moteur de calcul pour optimiser automatiquement
les Runes, Sigils et Stats d'un build en testant mathématiquement
toutes les combinaisons possibles.

FOCUS: WvW/McM uniquement (pas de PvE).
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from app.core.logging import logger
from app.engine.combat.context import CombatContext
from app.engine.simulation.calculator import BuildCalculator
from app.engine.gear.registry import RUNE_REGISTRY, SIGIL_REGISTRY, RELIC_REGISTRY
from app.engine.modifiers.base import Modifier, ModifierType
from app.services.gw2_data_store import GW2DataStore
from app.engine.simulation.rotation import RotationSimulator, RotationSkill


@dataclass
class OptimizationResult:
    """Résultat d'une optimisation de build."""
    
    rune_name: str
    sigil_names: List[str]
    total_damage: float
    dps_increase_percent: float
    survivability_score: float
    overall_score: float
    breakdown: Dict[str, Any]
    relic_name: Optional[str] = None


class BuildEquipmentOptimizer:
    """
    Optimiseur d'équipement pour builds GW2 WvW.
    
    Teste automatiquement différentes combinaisons de runes/sigils
    et utilise le moteur de calcul pour trouver l'optimal.
    
    WvW Context:
    - 25 Might (boon bot présent)
    - Fury uptime ~80%
    - 25 Vulnerability sur cible (focus fire)
    - Heavy Armor targets (meta comps)
    """
    
    def __init__(self):
        self.calculator = BuildCalculator()
        self.rotation_simulator = RotationSimulator()
        self.wvw_context = self._create_wvw_context()
        self.data_store = GW2DataStore()
    
    def _create_wvw_context(self) -> CombatContext:
        """Crée un contexte WvW réaliste."""
        return self._create_wvw_context_for_mode("wvw_zerg")

    def _create_wvw_context_for_mode(self, mode: Optional[str]) -> CombatContext:
        m = (mode or "wvw_zerg").lower()
        if m == "wvw_roam":
            ctx = CombatContext.create_default(might_stacks=18, fury=True)
            ctx.add_boon("Quickness", 1, 1)
            ctx.set_boon_uptime("Quickness", 0.5)
            ctx.target_armor = 2271
            ctx.add_condition_to_target("Vulnerability", 10)
        elif m == "wvw_outnumber":
            ctx = CombatContext.create_default(might_stacks=22, fury=True)
            ctx.add_boon("Quickness", 1, 1)
            ctx.add_boon("Protection", 1, 1)
            ctx.set_boon_uptime("Quickness", 0.7)
            ctx.set_boon_uptime("Protection", 0.7)
            ctx.target_armor = 2597
            ctx.add_condition_to_target("Vulnerability", 15)
        else:
            ctx = CombatContext.create_default(might_stacks=25, fury=True)
            ctx.add_boon("Quickness", 1, 1)
            ctx.add_boon("Protection", 1, 1)
            ctx.set_boon_uptime("Quickness", 0.9)
            ctx.set_boon_uptime("Protection", 0.9)
            ctx.target_armor = 2597
            ctx.add_condition_to_target("Vulnerability", 25)
        ctx.in_combat = True
        return ctx

    def set_mode(self, mode: str) -> None:
        self.wvw_context = self._create_wvw_context_for_mode(mode)

    def _context_for_constraints(self, constraints: Optional[Dict[str, Any]]) -> CombatContext:
        """Déduit le contexte WvW à utiliser à partir des contraintes éventuelles.

        Permet par exemple de choisir entre zerg / outnumber / roam sans
        toucher au contexte global partagé par les autres appels.
        """
        if constraints and isinstance(constraints, dict):
            mode_val = constraints.get("mode")
            if isinstance(mode_val, str) and mode_val:
                return self._create_wvw_context_for_mode(mode_val)
        return self.wvw_context
    
    async def optimize_build(
        self,
        base_stats: Dict[str, int],
        skill_rotation: List[Dict[str, Any]],
        role: str = "dps",  # dps, support, tank
        constraints: Optional[Dict[str, Any]] = None,
    ) -> OptimizationResult:
        """
        Optimise l'équipement d'un build pour WvW.
        
        Args:
            base_stats: Stats de base (gear Berserker/Viper/etc.)
            skill_rotation: Liste des skills utilisés (coefficients)
            role: Rôle du build (dps, support, tank)
            constraints: Contraintes optionnelles (ex: "must_have_scholar")
        
        Returns:
            OptimizationResult avec la meilleure combinaison
        """
        # Pour compatibilité, on délègue à la version top_k et on retourne le meilleur.
        top_candidates = await self.optimize_build_top_k(
            base_stats=base_stats,
            skill_rotation=skill_rotation,
            role=role,
            constraints=constraints,
            top_k=3,
        )

        # Journalisation du meilleur résultat (comportement proche de l'ancien)
        if not top_candidates:
            raise RuntimeError("No optimization candidates generated; check runes/sigils configuration.")

        best_result = top_candidates[0]
        logger.info(
            f"✅ Optimization complete! Best: {best_result.rune_name} + "
            f"{best_result.sigil_names} (Score: {best_result.overall_score:.2f})"
        )

        return best_result

    async def optimize_build_top_k(
        self,
        base_stats: Dict[str, int],
        skill_rotation: List[Dict[str, Any]],
        role: str = "dps",
        constraints: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> List[OptimizationResult]:
        """Retourne les K meilleures combinaisons pour un build donné.

        Cette méthode parcourt le même espace de recherche que optimize_build
        mais renvoie les K meilleurs candidats triés par score global, afin
        de permettre à un agent supérieur (Build Advisor) de choisir selon
        le contexte (débutant, zerg, roam, etc.).
        """
        logger.info(
            f"🔧 Optimizing build (top_k={top_k}) for role: {role} (WvW context)"
        )

        runes_to_test = self.get_runes_for_role(role)

        # Récupérer la préférence d'arme éventuelle pour affiner les sigils
        weapon_pref: Optional[str] = None
        if constraints and isinstance(constraints, dict):
            wp = constraints.get("weapon_preference")
            if isinstance(wp, str) and wp.strip():
                weapon_pref = wp.strip()

        sigils_for_role = self.get_sigils_for_role(role)
        if weapon_pref:
            sigils_to_test = self._filter_sigils_for_weapon(sigils_for_role, weapon_pref)
        else:
            sigils_to_test = sigils_for_role

        tested_combinations: List[OptimizationResult] = []

        # Contexte spécifique éventuel pour ce run (mode roam/outnumber/zerg)
        context_for_run = self._context_for_constraints(constraints)

        for rune_name in runes_to_test:
            for sigil_combo in self._generate_sigil_combinations(sigils_to_test):
                result = await self._test_combination(
                    base_stats=base_stats,
                    rune_name=rune_name,
                    sigil_names=sigil_combo,
                    skill_rotation=skill_rotation,
                    role=role,
                    context=context_for_run,
                )
                tested_combinations.append(result)

        if not tested_combinations:
            logger.warning("No combinations tested in optimize_build_top_k.")
            return []

        sorted_combos = sorted(
            tested_combinations,
            key=lambda x: x.overall_score,
            reverse=True,
        )

        # Normaliser top_k
        k = max(1, top_k)
        top_candidates = sorted_combos[:k]

        logger.info("🏆 Top combinations:")
        for i, res in enumerate(top_candidates, 1):
            logger.info(
                f"   {i}. {res.rune_name} + {res.sigil_names}: "
                f"Score {res.overall_score:.2f} (+{res.dps_increase_percent:.1f}% DPS)"
            )

        return top_candidates
    
    async def _test_combination(
        self,
        base_stats: Dict[str, int],
        rune_name: str,
        sigil_names: List[str],
        skill_rotation: List[Dict[str, Any]],
        role: str,
        context: Optional[CombatContext] = None,
    ) -> OptimizationResult:
        """Teste une combinaison spécifique de rune + sigils."""
        ctx = context or self.wvw_context

        # Créer les modifiers
        modifiers = []
        
        relic_name = self.get_relic_for_role(role)

        # Ajouter la rune
        if rune_name in RUNE_REGISTRY:
            modifiers.extend(RUNE_REGISTRY[rune_name]())
        
        # Ajouter les sigils
        for sigil_name in sigil_names:
            if sigil_name in SIGIL_REGISTRY:
                sigil_func = SIGIL_REGISTRY[sigil_name]
                # Gérer le cas Bloodlust (besoin de stacks)
                if sigil_name == "Bloodlust":
                    modifiers.append(sigil_func(25))  # Max stacks pour WvW
                else:
                    modifiers.append(sigil_func())

        # Ajouter la relique
        if relic_name and relic_name in RELIC_REGISTRY:
            try:
                modifiers.extend(RELIC_REGISTRY[relic_name]())
            except Exception as e:  # pragma: no cover - sécurité
                logger.error(f"Failed to build modifiers for relic {relic_name}: {e}")
                relic_name = None
        
        # Calculer les stats effectives
        effective_stats = self.calculator.calculate_effective_stats(
            base_stats=base_stats,
            modifiers=modifiers,
            context=ctx,
        )
        
        # Calculer le DPS total sur la rotation (approximation simple, 1 cast par skill)
        total_damage = 0.0
        for skill in skill_rotation:
            result = self.calculator.calculate_skill_damage(
                skill_data=skill,
                effective_stats=effective_stats,
                context=ctx,
            )
            total_damage += result["total_damage"]

        # Simulation de rotation sur timeline (non utilisée dans le score global pour l'instant)
        rotation_skills: List[RotationSkill] = []
        for idx, skill in enumerate(skill_rotation):
            if not isinstance(skill, dict):
                continue
            coef = skill.get("damage_coefficient")
            if not isinstance(coef, (int, float)):
                continue
            raw_name = skill.get("name")
            if isinstance(raw_name, str) and raw_name:
                name = raw_name
            else:
                name = f"Skill {idx + 1}"
            cast_time = skill.get("cast_time", 1.0)
            cooldown = skill.get("cooldown", 8.0)
            priority_val = skill.get("priority", idx)
            conditions = skill.get("conditions")
            heal_coef = skill.get("heal_coefficient", 0.0)
            base_heal = skill.get("base_heal", 0.0)
            try:
                rs = RotationSkill(
                    name=name,
                    damage_coefficient=float(coef),
                    cast_time=float(cast_time),
                    cooldown=float(cooldown),
                    conditions=conditions if isinstance(conditions, dict) else None,
                    priority=int(priority_val),
                    heal_coefficient=float(heal_coef) if isinstance(heal_coef, (int, float)) else 0.0,
                    base_heal=float(base_heal) if isinstance(base_heal, (int, float)) else 0.0,
                )
            except Exception:
                continue
            rotation_skills.append(rs)

        rotation_dps: Optional[float] = None
        rotation_total_damage: Optional[float] = None
        rotation_hps: Optional[float] = None
        rotation_total_heal: Optional[float] = None
        if rotation_skills:
            try:
                sim_result = self.rotation_simulator.simulate_rotation(
                    base_stats=base_stats,
                    modifiers=modifiers,
                    context=ctx,
                    skills=rotation_skills,
                    duration=10.0,
                    weapon_strength=1000,
                    effective_stats=effective_stats,
                )
                rotation_dps = float(sim_result.get("dps", 0.0))
                rotation_total_damage = float(sim_result.get("total_damage", 0.0))
                rotation_hps = float(sim_result.get("hps", 0.0))
                rotation_total_heal = float(sim_result.get("total_heal", 0.0))
            except Exception:
                rotation_dps = None
                rotation_total_damage = None
                rotation_hps = None
                rotation_total_heal = None

        # Calculer DPS increase (vs base sans runes/sigils)
        base_damage = self._calculate_base_damage(base_stats, skill_rotation, context=ctx)
        dps_increase = ((total_damage - base_damage) / base_damage) * 100 if base_damage > 0 else 0
        
        # Calculer survivability score (pour role tank/support)
        survivability = self._calculate_survivability_score(
            effective_stats, modifiers, role
        )
        
        # Score global pondéré selon le rôle
        overall_score = self._calculate_overall_score(
            total_damage,
            survivability,
            role,
            effective_stats,
            modifiers,
        )
        
        return OptimizationResult(
            rune_name=rune_name,
            sigil_names=sigil_names,
            total_damage=total_damage,
            dps_increase_percent=dps_increase,
            survivability_score=survivability,
            overall_score=overall_score,
            breakdown={
                "effective_power": effective_stats["effective_power"],
                "crit_chance": effective_stats["crit_chance"],
                "crit_damage": effective_stats["crit_damage_multiplier"],
                "damage_multiplier": effective_stats.get("damage_multiplier", 1.0),
                "effective_condition_damage": effective_stats["effective_condition_damage"],
                "rotation_dps_10s": rotation_dps,
                "rotation_total_damage_10s": rotation_total_damage,
                "rotation_hps_10s": rotation_hps,
                "rotation_total_heal_10s": rotation_total_heal,
            },
            relic_name=relic_name,
        )

    def _calculate_base_damage(
        self,
        base_stats: Dict[str, int],
        skill_rotation: List[Dict[str, Any]],
        context: Optional[CombatContext] = None,
    ) -> float:
        """Calcule le DPS de base sans runes/sigils."""
        # Stats effectives avec boons seulement (pas de runes/sigils)
        ctx = context or self.wvw_context
        effective_stats = self.calculator.calculate_effective_stats(
            base_stats=base_stats,
            modifiers=[],  # Pas de modifiers
            context=ctx,
        )

        total = 0.0
        for skill in skill_rotation:
            result = self.calculator.calculate_skill_damage(
                skill_data=skill,
                effective_stats=effective_stats,
                context=ctx,
            )
            total += result["total_damage"]

        return total

    def _calculate_survivability_score(
        self, effective_stats: Dict[str, float], modifiers: List[Modifier], role: str
    ) -> float:
        """Calcule un score de survie basé sur toughness, healing, etc."""
        toughness = effective_stats.get("toughness", 1000)
        max_health = effective_stats.get("max_health", 15000)
        healing_power = effective_stats.get("healing_power", 0)
        incoming_mult = effective_stats.get("incoming_damage_multiplier", 1.0) or 1.0
        has_scholar = any("Scholar" in m.name for m in modifiers)
        scholar_penalty = 0.8 if has_scholar else 1.0
        # Soft cap sur les HP pour éviter de survaloriser la vitalité à très haut niveau.
        #  - Jusqu'à 20k HP: valeur pleine
        #  - 20k-25k HP: chaque point compte à 50%
        #  - Au-delà de 25k HP: chaque point compte à 10%
        base_hp = min(float(max_health), 20000.0)
        mid_hp = min(max(float(max_health) - 20000.0, 0.0), 5000.0)
        high_hp = max(float(max_health) - 25000.0, 0.0)
        hp_score = (base_hp / 15000.0) + (mid_hp / 15000.0 * 0.5) + (high_hp / 15000.0 * 0.1)

        base = (toughness / 1000.0) + hp_score + (healing_power / 1000.0)
        mitigation_mult = 1.0 / incoming_mult if incoming_mult > 0 else 1.0
        return base * mitigation_mult * scholar_penalty
    
    def _normalize_role(self, role: str) -> str:
        """Normalise le rôle en catégories internes (dps, heal, boon, tank, support).

        Cette normalisation permet de rester compatible avec les appels
        existants ("dps", "support", "tank") tout en supportant des rôles
        plus fins comme "heal" ou "boon" provenant d'autres agents.
        """
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

    def _normalize_rune_name_from_api(self, full_name: str) -> Optional[str]:
        """Convertit un nom de rune GW2 API en clé interne du registre.

        Exemple: "Superior Rune of the Scholar" -> "Scholar".
        """
        name = full_name or ""
        if "Rune of " in name:
            # Ne garder que la partie après "Rune of "
            name = name.split("Rune of ", 1)[1]

        # Retirer les préfixes de rareté
        for prefix in ("Superior ", "Major ", "Minor "):
            if name.startswith(prefix):
                name = name[len(prefix) :]

        # Retirer l'article initial éventuel
        for article in ("the ", "The "):
            if name.startswith(article):
                name = name[len(article) :]

        name = name.strip()
        return name or None

    def get_runes_for_role(self, role: str) -> List[str]:
        """Retourne les runes candidates pour un rôle donné en s'appuyant sur les données GW2.

        Si les données locales sont indisponibles ou ne couvrent aucune rune connue
        du moteur, on retombe sur le comportement historique basé uniquement sur
        le registre interne des runes.
        """
        try:
            runes = self.data_store.get_runes()
        except Exception as e:  # pragma: no cover - garde-fou
            logger.error(f"GW2DataStore error while loading runes: {e}")
            return self._get_wvw_meta_runes(role)

        available_names: set[str] = set()
        for comp in runes:
            api_name = comp.get("name")
            if not isinstance(api_name, str):
                continue
            short = self._normalize_rune_name_from_api(api_name)
            if short and short in RUNE_REGISTRY:
                available_names.add(short)

        if not available_names:
            logger.warning(
                "GW2DataStore returned no matching runes; falling back to registry-only list."
            )
            return self._get_wvw_meta_runes(role)

        return self._get_wvw_meta_runes(role, allowed_names=available_names)

    def _normalize_sigil_name_from_api(self, full_name: str) -> Optional[str]:
        """Convertit un nom de sigil GW2 API en clé interne du registre.

        Exemple: "Superior Sigil of Force" -> "Force".
        """
        name = full_name or ""
        if "Sigil of " in name:
            # Ne garder que la partie après "Sigil of "
            name = name.split("Sigil of ", 1)[1]

        for prefix in ("Superior ", "Major ", "Minor "):
            if name.startswith(prefix):
                name = name[len(prefix) :]

        for article in ("the ", "The "):
            if name.startswith(article):
                name = name[len(article) :]

        name = name.strip()
        return name or None

    def get_sigils_for_role(self, role: str) -> List[str]:
        """Retourne les sigils candidats pour un rôle donné en s'appuyant sur les données GW2.

        Comme pour les runes, si aucune correspondance n'est trouvée ou si les
        données locales sont indisponibles, on retombe sur la logique
        historique basée uniquement sur le registre interne.
        """
        try:
            sigils = self.data_store.get_sigils()
        except Exception as e:  # pragma: no cover - garde-fou
            logger.error(f"GW2DataStore error while loading sigils: {e}")
            return self._get_wvw_meta_sigils(role)

        available_names: set[str] = set()
        for comp in sigils:
            api_name = comp.get("name")
            if not isinstance(api_name, str):
                continue
            short = self._normalize_sigil_name_from_api(api_name)
            if short and short in SIGIL_REGISTRY:
                available_names.add(short)

        if not available_names:
            logger.warning(
                "GW2DataStore returned no matching sigils; falling back to registry-only list."
            )
            return self._get_wvw_meta_sigils(role)

        return self._get_wvw_meta_sigils(role, allowed_names=available_names)

    def _normalize_relic_name_from_api(self, full_name: str) -> Optional[str]:
        """Convertit un nom de relique GW2 API en clé interne du registre.

        Exemple: "Relic of the Fireworks" -> "Fireworks".
        """

        name = full_name or ""
        if "Relic of " in name:
            name = name.split("Relic of ", 1)[1]

        for article in ("the ", "The "):
            if name.startswith(article):
                name = name[len(article) :]

        name = name.strip()
        return name or None

    def get_relic_for_role(self, role: str) -> Optional[str]:
        """Sélectionne une relique adaptée à un rôle donné en utilisant les données GW2.

        On choisit une seule relique par build, en privilégiant un petit
        sous-ensemble meta et en respectant la disponibilité dans relics.json.
        """

        try:
            relic_items = self.data_store.get_relics()
        except Exception as e:  # pragma: no cover - garde-fou
            logger.error(f"GW2DataStore error while loading relics: {e}")
            return None

        available_names: set[str] = set()
        for it in relic_items:
            api_name = it.get("name")
            if not isinstance(api_name, str):
                continue
            short = self._normalize_relic_name_from_api(api_name)
            if short and short in RELIC_REGISTRY:
                available_names.add(short)

        if not available_names:
            logger.warning("GW2DataStore returned no matching relics; no relic will be applied.")
            return None

        role_cat = self._normalize_role(role)
        preferred_order = {
            "dps": ["Fireworks"],
            "boon": ["Herald", "Monk"],
            "heal": ["Flock", "Monk"],
            "tank": ["Centaur", "Scourge"],
            "support": ["Herald", "Flock"],
        }

        for name in preferred_order.get(role_cat, preferred_order["dps"]):
            if name in available_names:
                return name

        # Fallback: choisir arbitrairement une relique disponible pour éviter de ne rien appliquer
        chosen = sorted(available_names)[0]
        logger.info(f"No preferred relic found for role {role_cat}; falling back to {chosen}.")
        return chosen

    def _calculate_overall_score(
        self,
        damage: float,
        survivability: float,
        role: str,
        effective_stats: Dict[str, float],
        modifiers: List[Modifier],
    ) -> float:
        """Calcule un score global spécialisé selon le rôle.

        Objectifs par rôle (approximation V1.5):
          - DPS      : maximiser les dégâts bruts.
          - HEAL     : maximiser healing_power + %healing sortant + survie.
          - BOON     : maximiser la durée de boon + survie.
          - TANK/STAB: maximiser l'EHP (toughness + health) + survie.
          - SUPPORT  : hybride DPS/boon/survie.
        """
        role_cat = self._normalize_role(role)

        # Contexte pour évaluer certains modificateurs (boon, healing).
        context_dict = self.wvw_context.to_dict()

        # Agrégats dérivés disponibles
        healing_power = float(effective_stats.get("healing_power", 0.0))
        boon_duration_bonus = float(effective_stats.get("boon_duration_bonus", 0.0))
        toughness = float(effective_stats.get("toughness", 0.0))
        max_health = float(effective_stats.get("max_health", 0.0))

        # Bonus issus des runes/sigils (non couverts par les stats dérivées)
        outgoing_heal_bonus = 0.0
        boon_duration_from_mods = 0.0
        for m in modifiers:
            if m.modifier_type == ModifierType.OUTGOING_HEALING:
                outgoing_heal_bonus += m.get_effective_value(context_dict)
            elif m.modifier_type == ModifierType.BOON_DURATION:
                boon_duration_from_mods += m.get_effective_value(context_dict)

        total_boon_duration = boon_duration_bonus + boon_duration_from_mods
        # Cap grosso modo à +100% (1.0) pour éviter les scores absurdes
        capped_boon = min(total_boon_duration, 1.0)

        # DPS pur: combiner dégâts directs et potentiel dégâts par altération
        if role_cat == "dps":
            condi_stat = float(effective_stats.get("effective_condition_damage", 0.0))
            # Poids modéré pour encourager les builds Condi sans écraser le strike
            condi_bonus = condi_stat * 8.0
            return damage + condi_bonus

        # Healer: privilégier le soin + %healing sortant + survie
        if role_cat == "heal":
            # Bonus/pénalité doux selon les HP max pour éviter les healers en carton (ex: full Cleric sans vitalité)
            max_hp = float(max_health)
            # Cible raisonnable ~ 18k-22k HP ; en dessous d'un certain seuil, on pénalise légèrement.
            hp_penalty_factor = 1.0
            if max_hp < 16000.0:
                hp_penalty_factor = 0.8
            elif max_hp < 18000.0:
                hp_penalty_factor = 0.9

            return (
                (healing_power * hp_penalty_factor)
                + outgoing_heal_bonus * 10000.0
                + survivability * 500.0
            )

        # Boon share: priorité à la durée de boon + survie
        if role_cat == "boon":
            return capped_boon * 10000.0 + survivability * 400.0

        # Tank / Stab: EHP approximé + survie
        if role_cat == "tank":
            return toughness * 2.0 + (max_health / 10.0) + survivability * 500.0

        # Support générique (hybride boon/heal/dps)
        if role_cat == "support":
            return (
                damage * 0.5
                + capped_boon * 5000.0
                + survivability * 600.0
            )

        # Fallback générique
        return (damage * 0.6) + (survivability * 400.0)
    
    def _get_wvw_meta_runes(self, role: str, allowed_names: Optional[set[str]] = None) -> List[str]:
        """Sélectionne les runes WvW adaptées à un rôle donné.

        Logique V1.5:
          - Parcourt le registre complet de runes.
          - Classe chaque rune selon les stats qu'elle apporte.
          - Filtre large mais logique pour éviter les non-sens flagrants
            (ex: rune 100% DPS sur un pur healer).
        """
        role_cat = self._normalize_role(role)
        selected: List[str] = []

        for name, factory in RUNE_REGISTRY.items():
            if allowed_names is not None and name not in allowed_names:
                continue
            mods = factory()

            has_heal = any(
                (m.target_stat in ("healing_power",) and m.modifier_type in {ModifierType.FLAT_STAT, ModifierType.PERCENT_STAT})
                or m.modifier_type in {ModifierType.OUTGOING_HEALING, ModifierType.INCOMING_HEALING}
                for m in mods
            )
            has_boon = any(
                m.modifier_type == ModifierType.BOON_DURATION
                or m.target_stat == "concentration"
                for m in mods
            )
            has_tank = any(
                m.target_stat in ("toughness", "vitality")
                for m in mods
            )
            has_dps = any(
                (m.target_stat in ("power", "precision", "ferocity", "condition_damage"))
                or m.modifier_type
                in {
                    ModifierType.DAMAGE_MULTIPLIER,
                    ModifierType.STRIKE_DAMAGE_MULTIPLIER,
                    ModifierType.CONDITION_DAMAGE_MULTIPLIER,
                    ModifierType.PROC_DAMAGE,
                }
                for m in mods
            )

            if role_cat == "heal":
                if has_heal or has_boon:
                    selected.append(name)
            elif role_cat == "boon":
                if has_boon or has_heal:
                    selected.append(name)
            elif role_cat == "tank":
                if has_tank or has_boon:
                    selected.append(name)
            elif role_cat == "support":
                if has_heal or has_boon or (has_tank and not has_dps):
                    selected.append(name)
            else:  # dps / défaut
                if has_dps:
                    selected.append(name)

        # Fallbacks si le filtre est trop strict
        if not selected:
            if role_cat == "heal":
                return ["Monk", "Water", "Druid"]
            if role_cat == "boon":
                return ["Herald", "Chronomancer", "Aristocracy", "Strength"]
            if role_cat == "tank":
                return ["Durability", "Ogre", "Dolyak"]
            # dps / support: garder le comportement historique
            return ["Scholar", "Eagle", "Hoelbrak", "Strength"]

        return selected
    
    def _get_wvw_meta_sigils(self, role: str, allowed_names: Optional[set[str]] = None) -> List[str]:
        """Sélectionne les sigils WvW adaptés à un rôle donné.

        Même philosophie que pour les runes: filtrage basé sur les stats
        (power/crit pour DPS, healing/boon pour support, toughness/vitality
        pour tank), sans être trop restrictif.
        """
        role_cat = self._normalize_role(role)
        selected: List[str] = []

        for name, factory in SIGIL_REGISTRY.items():
            if allowed_names is not None and name not in allowed_names:
                continue
            try:
                mod = factory()
            except TypeError:
                # Certains sigils (ex: Bloodlust) acceptent des paramètres
                mod = factory(25)  # type: ignore[misc]

            has_heal = mod.target_stat == "healing_power" or mod.modifier_type in {
                ModifierType.OUTGOING_HEALING,
                ModifierType.INCOMING_HEALING,
            }
            has_boon = mod.modifier_type == ModifierType.BOON_DURATION or mod.target_stat == "concentration"
            has_tank = mod.target_stat in {"toughness", "vitality"}
            has_dps = (
                mod.target_stat in {"power", "precision", "ferocity", "condition_damage"}
                or mod.modifier_type
                in {
                    ModifierType.DAMAGE_MULTIPLIER,
                    ModifierType.STRIKE_DAMAGE_MULTIPLIER,
                    ModifierType.CONDITION_DAMAGE_MULTIPLIER,
                    ModifierType.PROC_DAMAGE,
                }
            )

            if role_cat == "heal":
                if has_heal or has_boon:
                    selected.append(name)
            elif role_cat == "boon":
                if has_boon or has_heal:
                    selected.append(name)
            elif role_cat == "tank":
                if has_tank or has_heal:
                    selected.append(name)
            elif role_cat == "support":
                if has_heal or has_boon or (has_tank and not has_dps):
                    selected.append(name)
            else:  # dps / défaut
                if has_dps:
                    selected.append(name)

        # Fallbacks si le filtre ne trouve rien (sécurité)
        if not selected:
            if role_cat == "heal":
                return ["Transference", "Leeching", "Draining", "Cleansing", "Concentration"]
            if role_cat == "boon":
                return ["Concentration", "Generosity", "Strength"]
            if role_cat == "tank":
                return ["Absorption", "Draining", "Leeching"]
            # dps / support: liste historique
            return ["Force", "Bloodlust", "Impact", "Air", "Hydromancy"]

        return selected
    
    def _filter_sigils_for_weapon(self, sigils: List[str], weapon_preference: str) -> List[str]:
        weapon = (weapon_preference or "").lower()
        if not sigils or not weapon:
            return sigils

        # Groupes d'armes pour orienter le choix des sigils
        heavy_melee = {"hammer", "greatsword", "mace", "axe"}
        fast_melee = {"sword", "dagger"}
        ranged_power = {"rifle", "longbow", "shortbow", "pistol", "scepter"}
        support_weapons = {"staff", "shield", "focus", "torch", "warhorn"}

        preferred_for_heavy = ["Impact", "Force", "Air", "Hydromancy", "Bloodlust"]
        preferred_for_fast = ["Air", "Force", "Hydromancy", "Bloodlust"]
        preferred_for_ranged = ["Air", "Force", "Hydromancy", "Bloodlust"]
        preferred_for_support = ["Concentration", "Generosity", "Transference", "Cleansing", "Leeching"]

        prefs: List[str]
        if weapon in heavy_melee:
            prefs = preferred_for_heavy
        elif weapon in fast_melee:
            prefs = preferred_for_fast
        elif weapon in ranged_power:
            prefs = preferred_for_ranged
        elif weapon in support_weapons:
            prefs = preferred_for_support
        else:
            # Arme inconnue: ne pas filtrer du tout
            return sigils

        # Ne PAS exclure les autres sigils du moteur: on priorise simplement l'ordre
        prefs_set = set(prefs)
        preferred = [s for s in sigils if s in prefs_set]
        others = [s for s in sigils if s not in prefs_set]
        # On renvoie d'abord les sigils adaptés à l'arme, puis tous les autres
        return preferred + others
    
    def _generate_sigil_combinations(
        self, sigils: List[str], max_sigils: int = 2
    ) -> List[List[str]]:
        """Génère toutes les combinaisons de sigils (2 slots généralement)."""
        from itertools import combinations
        
        combos: List[List[str]] = []

        # Cas simple: un seul slot de sigil
        if max_sigils <= 1:
            for s in sigils:
                combos.append([s])
            return combos

        # Deux sigils différents uniquement (pas de doublons dans une même arme)
        for combo in combinations(sigils, max_sigils):
            if len(set(combo)) == len(combo):
                combos.append(list(combo))
        
        return combos


# Instance globale
_optimizer = None


def get_build_optimizer() -> BuildEquipmentOptimizer:
    """Get or create the global optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = BuildEquipmentOptimizer()
    return _optimizer
