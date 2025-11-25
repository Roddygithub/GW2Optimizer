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
from app.engine.gear.registry import RUNE_REGISTRY, SIGIL_REGISTRY
from app.engine.modifiers.base import Modifier


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
        self.wvw_context = self._create_wvw_context()
    
    def _create_wvw_context(self) -> CombatContext:
        """Crée un contexte WvW réaliste."""
        context = CombatContext.create_default(might_stacks=25, fury=True)
        context.add_condition_to_target("Vulnerability", 25)
        context.target_armor = 2597  # Heavy armor (meta)
        context.in_combat = True
        return context
    
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
        logger.info(f"🔧 Optimizing build for role: {role} (WvW context)")
        
        # Liste de runes à tester (WvW meta)
        runes_to_test = self._get_wvw_meta_runes(role)
        
        # Liste de sigils à tester (WvW meta)
        sigils_to_test = self._get_wvw_meta_sigils(role)
        
        best_result = None
        best_score = -float('inf')
        
        tested_combinations = []
        
        # Tester toutes les combinaisons
        for rune_name in runes_to_test:
            for sigil_combo in self._generate_sigil_combinations(sigils_to_test):
                result = await self._test_combination(
                    base_stats=base_stats,
                    rune_name=rune_name,
                    sigil_names=sigil_combo,
                    skill_rotation=skill_rotation,
                    role=role,
                )
                
                tested_combinations.append(result)
                
                if result.overall_score > best_score:
                    best_score = result.overall_score
                    best_result = result
        
        logger.info(
            f"✅ Optimization complete! Best: {best_result.rune_name} + "
            f"{best_result.sigil_names} (Score: {best_result.overall_score:.2f})"
        )
        
        # Log top 3 pour comparaison
        top_3 = sorted(tested_combinations, key=lambda x: x.overall_score, reverse=True)[:3]
        logger.info("🏆 Top 3 combinations:")
        for i, res in enumerate(top_3, 1):
            logger.info(
                f"   {i}. {res.rune_name} + {res.sigil_names}: "
                f"Score {res.overall_score:.2f} (+{res.dps_increase_percent:.1f}% DPS)"
            )
        
        return best_result
    
    async def _test_combination(
        self,
        base_stats: Dict[str, int],
        rune_name: str,
        sigil_names: List[str],
        skill_rotation: List[Dict[str, Any]],
        role: str,
    ) -> OptimizationResult:
        """Teste une combinaison spécifique de rune + sigils."""
        
        # Créer les modifiers
        modifiers = []
        
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
        
        # Calculer les stats effectives
        effective_stats = self.calculator.calculate_effective_stats(
            base_stats=base_stats,
            modifiers=modifiers,
            context=self.wvw_context,
        )
        
        # Calculer le DPS total sur la rotation
        total_damage = 0.0
        for skill in skill_rotation:
            result = self.calculator.calculate_skill_damage(
                skill_data=skill,
                effective_stats=effective_stats,
                context=self.wvw_context,
            )
            total_damage += result["total_damage"]
        
        # Calculer DPS increase (vs base sans runes/sigils)
        base_damage = self._calculate_base_damage(base_stats, skill_rotation)
        dps_increase = ((total_damage - base_damage) / base_damage) * 100 if base_damage > 0 else 0
        
        # Calculer survivability score (pour role tank/support)
        survivability = self._calculate_survivability_score(
            effective_stats, modifiers, role
        )
        
        # Score global pondéré selon le rôle
        overall_score = self._calculate_overall_score(
            total_damage, survivability, role
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
            },
        )
    
    def _calculate_base_damage(
        self, base_stats: Dict[str, int], skill_rotation: List[Dict[str, Any]]
    ) -> float:
        """Calcule le DPS de base sans runes/sigils."""
        # Stats effectives avec boons seulement (pas de runes/sigils)
        effective_stats = self.calculator.calculate_effective_stats(
            base_stats=base_stats,
            modifiers=[],  # Pas de modifiers
            context=self.wvw_context,
        )
        
        total = 0.0
        for skill in skill_rotation:
            result = self.calculator.calculate_skill_damage(
                skill_data=skill,
                effective_stats=effective_stats,
                context=self.wvw_context,
            )
            total += result["total_damage"]
        
        return total
    
    def _calculate_survivability_score(
        self, effective_stats: Dict[str, float], modifiers: List[Modifier], role: str
    ) -> float:
        """Calcule un score de survie basé sur toughness, healing, etc."""
        # Simplifié pour l'instant
        toughness = effective_stats.get("toughness", 1000)
        max_health = effective_stats.get("max_health", 15000)
        healing_power = effective_stats.get("healing_power", 0)
        
        # Vérifier si Scholar est actif (requiert >90% health)
        has_scholar = any("Scholar" in m.name for m in modifiers)
        scholar_penalty = 0.8 if has_scholar else 1.0  # Scholar = moins tanky
        
        score = (toughness / 1000) + (max_health / 15000) + (healing_power / 1000)
        return score * scholar_penalty
    
    def _calculate_overall_score(
        self, damage: float, survivability: float, role: str
    ) -> float:
        """Score global pondéré selon le rôle."""
        if role == "dps":
            return (damage * 0.85) + (survivability * 0.15)
        elif role == "support":
            return (damage * 0.30) + (survivability * 0.70)
        elif role == "tank":
            return (damage * 0.20) + (survivability * 0.80)
        else:
            return (damage * 0.60) + (survivability * 0.40)
    
    def _get_wvw_meta_runes(self, role: str) -> List[str]:
        """Retourne les runes méta pour WvW selon le rôle."""
        if role == "dps":
            # DPS: Scholar (risqué), Eagle, Hoelbrak (safe alternatives)
            return ["Scholar", "Eagle", "Hoelbrak", "Strength"]
        elif role == "support":
            # Support: Monk (heal), Water (heal), Ogre (bruiser), Strength (might)
            return ["Monk", "Water", "Ogre", "Strength", "Durability"]
        elif role == "tank":
            # Tank: Durability, Ogre (all-around defense)
            return ["Durability", "Ogre", "Strength"]
        else:
            # Testez tout si rôle non spécifié
            return list(RUNE_REGISTRY.keys())
    
    def _get_wvw_meta_sigils(self, role: str) -> List[str]:
        """Retourne les sigils méta pour WvW selon le rôle."""
        if role == "dps":
            # DPS: Force (always), Bloodlust (stacking), Impact/Air (procs), Hydromancy (condi synergy)
            return ["Force", "Bloodlust", "Impact", "Air", "Hydromancy"]
        elif role == "support":
            # Support: Force (damage), Energy (mobility), Strength (might stacking)
            return ["Force", "Bloodlust", "Energy", "Strength"]
        elif role == "tank":
            # Tank: Absorption (shield), Energy (mobility), Battle (warrior adrenaline)
            return ["Force", "Absorption", "Energy", "Battle"]
        else:
            # Test common WvW sigils
            return ["Force", "Bloodlust", "Impact", "Air", "Energy", "Hydromancy"]
    
    def _generate_sigil_combinations(
        self, sigils: List[str], max_sigils: int = 2
    ) -> List[List[str]]:
        """Génère toutes les combinaisons de sigils (2 slots généralement)."""
        from itertools import combinations
        
        # 2 sigils différents
        combos = []
        for combo in combinations(sigils, max_sigils):
            combos.append(list(combo))
        
        # 1 sigil dans les 2 slots (si identique)
        for sigil in sigils:
            if sigil not in ["Force", "Bloodlust"]:  # Ces sigils ne stackent pas
                combos.append([sigil, sigil])
        
        return combos


# Instance globale
_optimizer = None


def get_build_optimizer() -> BuildEquipmentOptimizer:
    """Get or create the global optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = BuildEquipmentOptimizer()
    return _optimizer
