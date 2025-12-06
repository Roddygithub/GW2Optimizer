from __future__ import annotations

"""Gear preset service based on real GW2 items.

This module provides small, data-driven equipment presets built from the
local GW2 JSON dumps (items.json + itemstats.json). It is intentionally
read-only and lightweight: the combat engine continues to work purely on
aggregated stats; presets are only used for illustrative/example gear.
"""

from functools import lru_cache
from typing import Any, Dict, List

from app.models.build import Equipment
from app.services.gw2_data_store import GW2DataStore
from app.services.gear_prefix_validator import _normalize_itemstat_name


ARMOR_SLOTS_ORDER: List[str] = [
    "Helm",
    "Shoulders",
    "Coat",
    "Gloves",
    "Leggings",
    "Boots",
]


class GearPresetService:
    """Build small example armor sets for a given stat prefix.

    The goal is not to model every piece of gear, but to provide a
    realistic-looking set of items that correspond to a given prefix
    (e.g. Berserker, Minstrel, Diviner) using the official GW2 data.
    """

    def __init__(self, data_store: GW2DataStore | None = None) -> None:
        self._data_store = data_store or GW2DataStore()

    @lru_cache(maxsize=1)
    def _build_itemstats_index(self) -> Dict[int, List[str]]:
        """Index itemstat IDs to the set of normalized prefix names.

        Example: an itemstat named "Berserker's and Valkyrie" will yield
        {id: ["Berserker", "Valkyrie"]}.
        """

        index: Dict[int, List[str]] = {}
        itemstats = self._data_store.get_itemstats()
        if not itemstats:
            return index

        for entry in itemstats:
            stat_id = entry.get("id")
            name = entry.get("name")
            if not isinstance(stat_id, int) or not isinstance(name, str):
                continue
            prefixes = _normalize_itemstat_name(name)
            if not prefixes:
                continue
            index[stat_id] = sorted(prefixes)

        return index

    @lru_cache(maxsize=1)
    def _build_prefix_to_armor_index(self) -> Dict[str, List[Equipment]]:
        """Precompute a mapping prefix -> list of armor items.

        Each entry in the resulting lists is an Equipment model with
        slot/id/name/stats filled. Stats is set to the normalized prefix
        name (e.g. "Diviner").
        """

        mapping: Dict[str, List[Equipment]] = {}
        stat_index = self._build_itemstats_index()
        items = self._data_store.get_items()
        if not items or not stat_index:
            return mapping

        for it in items:
            if it.get("type") != "Armor":
                continue
            if it.get("level") != 80:
                continue

            game_types = it.get("game_types") or []
            if "Wvw" not in game_types:
                continue

            details: Dict[str, Any] = it.get("details") or {}
            armor_type = details.get("type")
            if armor_type not in ARMOR_SLOTS_ORDER:
                continue

            infix = details.get("infix_upgrade") or {}
            stat_id = infix.get("id")
            if not isinstance(stat_id, int):
                continue

            prefixes = stat_index.get(stat_id)
            if not prefixes:
                continue

            item_id = it.get("id")
            name = it.get("name")
            if not isinstance(item_id, int) or not isinstance(name, str):
                continue

            for prefix in prefixes:
                eq = Equipment(
                    slot=armor_type,
                    id=item_id,
                    name=name,
                    stats=prefix,
                    rune_or_sigil=None,
                )
                mapping.setdefault(prefix, []).append(eq)

        # Optionally, keep a deterministic order per prefix (by slot then id)
        for prefix, items_list in mapping.items():
            items_list.sort(key=lambda e: (ARMOR_SLOTS_ORDER.index(e.slot) if e.slot in ARMOR_SLOTS_ORDER else 99, e.id))

        return mapping

    def get_example_armor_for_prefix(self, prefix: str, max_items: int = 6) -> List[Equipment]:
        """Return a small example armor set for the given prefix.

        The result contains at most one item per armor slot, in the
        order defined by ARMOR_SLOTS_ORDER. If no data is available for
        the prefix, an empty list is returned.
        """

        index = self._build_prefix_to_armor_index()
        items = index.get(prefix)
        if not items:
            return []

        by_slot: Dict[str, Equipment] = {}
        for eq in items:
            if eq.slot in by_slot:
                continue
            by_slot[eq.slot] = eq
            if len(by_slot) >= max_items:
                break

        ordered: List[Equipment] = [by_slot[s] for s in ARMOR_SLOTS_ORDER if s in by_slot]
        return ordered


# Global convenience instance
_preset_service: GearPresetService | None = None


def get_gear_preset_service() -> GearPresetService:
    """Get or create the global GearPresetService instance."""

    global _preset_service
    if _preset_service is None:
        _preset_service = GearPresetService()
    return _preset_service
