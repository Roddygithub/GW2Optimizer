from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.gear.prefixes import get_all_prefixes
from app.services.gear_prefix_validator import filter_prefix_names_by_itemstats


# Slots used for piece-by-piece gear optimization. These names follow
# the GW2 API / items.json conventions and are aligned with
# GearPresetService.
ARMOR_SLOTS: List[str] = [
    "Helm",
    "Shoulders",
    "Coat",
    "Gloves",
    "Leggings",
    "Boots",
]

TRINKET_SLOTS: List[str] = [
    "Amulet",
    "Ring1",
    "Ring2",
    "Accessory1",
    "Accessory2",
    "Backpiece",
]

WEAPON_SLOTS: List[str] = [
    "WeaponA1",
    "WeaponA2",
    "WeaponB1",
    "WeaponB2",
]


@dataclass
class OptimizationConstraints:
    """Low-level stat constraints for the gear solver.

    Values are expressed directly in the same stat space as PREFIX_REGISTRY
    / itemstats.json (power, precision, vitality, etc.). A missing key means
    "no hard minimum" for that stat.
    """

    min_stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class EquipmentSet:
    """Piece-by-piece equipment assignment.

    The values are GW2 stat prefix names (e.g. "Berserker", "Minstrel").
    This structure is independent from actual GW2 item IDs; it only
    captures the distribution of prefixes per logical slot.
    """

    armor: Dict[str, str] = field(default_factory=dict)
    trinkets: Dict[str, str] = field(default_factory=dict)
    weapons: Dict[str, str] = field(default_factory=dict)

    def all_slots(self) -> Dict[str, str]:
        merged: Dict[str, str] = {}
        merged.update(self.armor)
        merged.update(self.trinkets)
        merged.update(self.weapons)
        return merged


@dataclass
class GearOptimizationResult:
    """Result of a gear optimization run.

    - equipment_set: chosen prefixes per slot
    - base_stats: aggregated stats for the whole set
    - constraints: constraints used for the search
    - score: overall heuristic score achieved by this configuration
    """

    equipment_set: EquipmentSet
    base_stats: Dict[str, int]
    constraints: OptimizationConstraints
    score: float


class GearOptimizationService:
    """Service responsible for piece-by-piece gear optimization.

    V1 focuses on armor slots only and uses a greedy heuristic. The
    public API is intentionally simple so it can later be used both by
    TeamCommanderAgent and offline training loops (AlphaGW2).
    """

    def __init__(self) -> None:
        # Snapshot of all prefixes (Berserker, Ritualist, Grieving, etc.)
        # discovered from GW2 itemstats.json. This map is shared between
        # optimization runs.
        self._all_prefixes: Dict[str, Dict[str, int]] = get_all_prefixes()

        # Keys used for all stat dicts (power, precision, vitality, ...)
        self._stat_keys: List[str] = []
        if self._all_prefixes:
            sample_stats = next(iter(self._all_prefixes.values()))
            self._stat_keys = list(sample_stats.keys())

        self._num_armor_slots: int = len(ARMOR_SLOTS)

    def derive_constraints(
        self,
        role: str,
        mode: str,
        experience: str,
    ) -> OptimizationConstraints:
        """Derive stat constraints from role/mode/experience.

        This is a heuristic layer that translates high-level intentions
        ("DPS beginner en zerg", "heal roam expert") into low-level
        minimums on stats (vitality, toughness, healing_power, etc.).
        """

        r = (role or "").lower()
        m = (mode or "wvw_zerg").lower()
        exp = (experience or "intermediate").lower()

        min_stats: Dict[str, int] = {}

        # Baselines par rôle
        if r in {"dps", "strip"}:
            # DPS: privilégier power/precision/ferocity avec un minimum de
            # vitalité pour éviter le full glass canon.
            min_stats["power"] = 2000
            min_stats["precision"] = 1700
            min_stats["ferocity"] = 600
            min_stats["vitality"] = 900
        elif r in {"heal", "support", "cleanse"}:
            # Supports/heals: focus soin + boon avec un peu de tankiness.
            min_stats["healing_power"] = 1400
            min_stats["concentration"] = 1100
            min_stats["vitality"] = 1200
            min_stats["toughness"] = 1000
        elif r == "boon":
            # Boon share: boon duration très élevée, un minimum de power et
            # de vitalité.
            min_stats["concentration"] = 1400
            min_stats["power"] = 1500
            min_stats["vitality"] = 1000
        else:
            # Tank / stab / hybride défensif.
            min_stats["toughness"] = 1500
            min_stats["vitality"] = 1500

        # Ajustement selon le niveau d'expérience
        if exp == "beginner":
            # Plus de sécurité (HP/armure) pour les débutants.
            if "vitality" in min_stats:
                min_stats["vitality"] = int(min_stats["vitality"] * 1.1)
            if "toughness" in min_stats:
                min_stats["toughness"] = int(min_stats["toughness"] * 1.1)
        elif exp == "expert":
            # Plus de greed sur les dégâts pour les joueurs expérimentés.
            if "vitality" in min_stats:
                min_stats["vitality"] = int(min_stats["vitality"] * 0.9)
            if "toughness" in min_stats:
                min_stats["toughness"] = int(min_stats["toughness"] * 0.9)
            if "power" in min_stats:
                min_stats["power"] = int(min_stats["power"] * 1.05)

        # Ajustement selon le mode de jeu
        if "outnumber" in m:
            # En infériorité numérique, on renforce la survie.
            if "vitality" in min_stats:
                min_stats["vitality"] += 200
            if "toughness" in min_stats:
                min_stats["toughness"] += 200
        elif "roam" in m:
            # Roaming: un petit bonus de survie, mais moins qu'en outnumber.
            if "vitality" in min_stats:
                min_stats["vitality"] += 100

        return OptimizationConstraints(min_stats=min_stats)

    def _normalize_role(self, role: str) -> str:
        """Normalise un rôle externe en catégories internes.

        Aligne la logique sur BuildEquipmentOptimizer pour rester cohérent
        avec le scoring par rôle.
        """

        r = (role or "").lower()
        if r in {"heal", "healer"}:
            return "heal"
        if r in {"boon", "boons"}:
            return "boon"
        if r in {"tank", "stab"}:
            return "tank"
        if r in {"support", "cleanse"}:
            return "support"
        if r in {"strip"}:
            return "dps"
        return "dps"

    def _select_candidate_prefixes_for_role(self, role_cat: str, mode: str) -> List[str]:
        """Sélectionne un sous-ensemble de préfixes pertinents pour un rôle.

        On réutilise la même philosophie que les presets de TeamCommander et
        BuildAnalysisService, mais en limitant le nombre de candidats pour
        garder l'algorithme glouton très rapide.
        """

        r = (role_cat or "").lower()
        m = (mode or "").lower()

        all_prefixes = self._all_prefixes or get_all_prefixes()

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
            if m == "wvw_roam":
                if "Celestial" in all_prefixes and "Celestial" not in candidates:
                    candidates.append("Celestial")
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
        else:  # tank / stab / fallback
            names = [
                name
                for name, stats in all_prefixes.items()
                if _is_tank(stats)
            ]
            if not names:
                names = ["Minstrel", "Soldier", "Trailblazer", "Dire"]

        # Filtrer par présence réelle dans itemstats.json
        filtered_names = filter_prefix_names_by_itemstats(names)
        candidates = [name for name in filtered_names if name in all_prefixes]

        if not candidates:
            candidates = [name for name in names if name in all_prefixes]

        if not candidates:
            candidates = sorted(all_prefixes.keys())

        # Trier les candidats par "affinité" avec le rôle
        def _role_axis(name: str) -> float:
            s = all_prefixes.get(name, {})
            power = float(s.get("power", 0))
            precision = float(s.get("precision", 0))
            ferocity = float(s.get("ferocity", 0))
            cond = float(s.get("condition_damage", 0))
            tough = float(s.get("toughness", 0))
            vita = float(s.get("vitality", 0))
            conc = float(s.get("concentration", 0))
            heal = float(s.get("healing_power", 0))

            if r == "dps":
                return power * 1.0 + precision * 0.7 + ferocity * 0.6 + cond * 0.4
            if r == "heal":
                return heal * 1.0 + conc * 0.7 + vita * 0.4
            if r == "boon":
                return conc * 1.0 + power * 0.5 + tough * 0.4
            if r == "tank":
                return tough * 1.0 + vita * 0.8 + heal * 0.3
            # support générique
            return (
                heal * 0.7
                + conc * 0.7
                + tough * 0.6
                + vita * 0.6
                + power * 0.3
            )

        candidates.sort(key=_role_axis, reverse=True)

        # Limiter le nombre de préfixes pour garder le solver très rapide
        MAX_CANDIDATES = 12
        return candidates[:MAX_CANDIDATES]

    def _choose_baseline_prefix(self, role_cat: str, candidates: List[str]) -> str:
        """Choisit un préfixe de base offensif pour démarrer la recherche.

        Pour les DPS, on privilégie Berserker puis Marauder/Valkyrie/Dragon.
        Pour les autres rôles, on choisit un préfixe méta raisonnable.
        """

        if not candidates:
            raise ValueError("No candidate prefixes available for gear optimization")

        r = (role_cat or "").lower()

        preferred_per_role = {
            "dps": ["Berserker", "Marauder", "Dragon", "Valkyrie", "Assassin", "Celestial"],
            "heal": ["Minstrel", "Harrier", "Cleric", "Magi", "Celestial"],
            "boon": ["Diviner", "Minstrel", "Harrier", "Celestial"],
            "tank": ["Soldier", "Trailblazer", "Dire", "Minstrel", "Celestial"],
            "support": ["Minstrel", "Harrier", "Celestial", "Cleric"],
        }

        ordered_candidates = candidates
        for name in preferred_per_role.get(r, []):
            if name in ordered_candidates:
                return name

        return ordered_candidates[0]

    def _compute_armor_stats_from_assignment(self, armor_assignment: Dict[str, str]) -> Dict[str, int]:
        """Agrège les stats d'un mapping slot -> prefix pour l'armure.

        Hypothèse V1: les valeurs de get_all_prefixes() représentent un set
        complet; chaque pièce d'armure contribue donc ~1/6 de ces stats.
        """

        if not self._all_prefixes:
            return {}

        if not self._stat_keys:
            sample_stats = next(iter(self._all_prefixes.values()))
            self._stat_keys = list(sample_stats.keys())

        totals: Dict[str, int] = {k: 0 for k in self._stat_keys}

        if self._num_armor_slots <= 0:
            return totals

        for slot, prefix in armor_assignment.items():
            stats = self._all_prefixes.get(prefix)
            if not stats:
                continue
            for key in self._stat_keys:
                base_val = stats.get(key, 0)
                contrib = int(round(float(base_val) / float(self._num_armor_slots)))
                totals[key] += contrib

        return totals

    def _evaluate_stats_for_role(
        self,
        stats: Dict[str, int],
        constraints: OptimizationConstraints,
        role_cat: str,
    ) -> float:
        """Calcule un score heuristique pour un set de stats.

        - pénalité élevée si les contraintes min_stats ne sont pas remplies;
        - à pénalité égale, on maximise un agrégat offensif adapté au rôle.
        """

        # Pénalité de contraintes non satisfaites
        penalty = 0.0
        for key, min_val in constraints.min_stats.items():
            actual = float(stats.get(key, 0))
            if actual < float(min_val):
                penalty += float(min_val) - actual

        # Agrégat offensif par rôle
        power = float(stats.get("power", 0))
        precision = float(stats.get("precision", 0))
        ferocity = float(stats.get("ferocity", 0))
        cond = float(stats.get("condition_damage", 0))
        tough = float(stats.get("toughness", 0))
        vita = float(stats.get("vitality", 0))
        conc = float(stats.get("concentration", 0))
        heal = float(stats.get("healing_power", 0))

        r = (role_cat or "").lower()

        if r == "dps":
            offense = power * 1.0 + precision * 0.8 + ferocity * 0.7 + cond * 0.4
        elif r == "heal":
            offense = heal * 1.0 + conc * 0.7 + vita * 0.5
        elif r == "boon":
            offense = conc * 1.0 + power * 0.5 + tough * 0.5
        elif r == "tank":
            offense = tough * 1.0 + vita * 0.9 + heal * 0.3
        else:  # support générique
            offense = (
                heal * 0.8
                + conc * 0.8
                + tough * 0.6
                + vita * 0.6
                + power * 0.3
            )

        # Les contraintes sont prioritaires: un petit manque coûte très cher.
        score = offense - penalty * 100.0
        return score

    def generate_equipment_set(
        self,
        role: str,
        profession: str,
        specialization: str,
        mode: str,
        experience: str,
    ) -> GearOptimizationResult:
        """Greedy armor-piece gear optimization entrypoint (V1).

        Algo glouton simplifié:
          1. Normaliser le rôle (dps/heal/boon/tank/support).
          2. Choisir quelques préfixes candidats adaptés au rôle.
          3. Démarrer en full préfixe offensif (ex: Berserker pour DPS).
          4. Tant qu'on trouve un slot + préfixe qui améliore le score
             (moins de pénalité de contraintes, ou même pénalité mais plus
             d'offense), on applique la modification.
        """

        if not self._all_prefixes:
            raise ValueError("No prefixes available for gear optimization")

        constraints = self.derive_constraints(role, mode, experience)
        role_cat = self._normalize_role(role)

        # 1) Préfixes candidats pour ce rôle + mode
        candidate_prefixes = self._select_candidate_prefixes_for_role(role_cat, mode)
        if not candidate_prefixes:
            candidate_prefixes = sorted(self._all_prefixes.keys())

        # 2) Préfixe de départ offensif (ex: full Berserker pour dps)
        base_prefix = self._choose_baseline_prefix(role_cat, candidate_prefixes)
        if base_prefix not in candidate_prefixes:
            candidate_prefixes = [base_prefix] + [p for p in candidate_prefixes if p != base_prefix]

        # 3) Configuration initiale: full base_prefix sur les 6 pièces d'armure
        current_armor: Dict[str, str] = {slot: base_prefix for slot in ARMOR_SLOTS}
        current_stats = self._compute_armor_stats_from_assignment(current_armor)
        current_score = self._evaluate_stats_for_role(current_stats, constraints, role_cat)

        # 4) Boucle gloutonne: pour chaque slot, tester tous les préfixes
        #    candidats et ne garder que les améliorations de score.
        max_iterations = max(1, len(ARMOR_SLOTS) * 4)
        for _ in range(max_iterations):
            best_neighbor_score = current_score
            best_neighbor_assignment: Optional[Dict[str, str]] = None
            best_neighbor_stats: Optional[Dict[str, int]] = None

            for slot in ARMOR_SLOTS:
                current_prefix = current_armor.get(slot, base_prefix)
                for prefix in candidate_prefixes:
                    if prefix == current_prefix:
                        continue

                    new_armor = dict(current_armor)
                    new_armor[slot] = prefix
                    new_stats = self._compute_armor_stats_from_assignment(new_armor)
                    new_score = self._evaluate_stats_for_role(new_stats, constraints, role_cat)

                    if new_score > best_neighbor_score + 1e-6:
                        best_neighbor_score = new_score
                        best_neighbor_assignment = new_armor
                        best_neighbor_stats = new_stats

            if best_neighbor_assignment is None or best_neighbor_stats is None:
                break

            current_armor = best_neighbor_assignment
            current_stats = best_neighbor_stats
            current_score = best_neighbor_score

        armor = current_armor
        trinkets: Dict[str, str] = {}
        weapons: Dict[str, str] = {}

        equipment_set = EquipmentSet(armor=armor, trinkets=trinkets, weapons=weapons)

        base_stats = current_stats

        return GearOptimizationResult(
            equipment_set=equipment_set,
            base_stats=base_stats,
            constraints=constraints,
            score=current_score,
        )


# Global convenience instance
_gear_opt_service: Optional[GearOptimizationService] = None


def get_gear_optimization_service() -> GearOptimizationService:
    """Get or create the global GearOptimizationService instance."""

    global _gear_opt_service
    if _gear_opt_service is None:
        _gear_opt_service = GearOptimizationService()
    return _gear_opt_service
