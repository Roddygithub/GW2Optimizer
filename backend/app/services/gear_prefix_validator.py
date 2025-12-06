from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Set, Dict, Any

from app.core.logging import logger
from app.engine.gear.prefixes import PREFIX_REGISTRY
from app.services.gw2_data_store import GW2DataStore


def _normalize_itemstat_name(raw_name: str) -> Set[str]:
    """Normalize an itemstat name to one or more prefix keys.

    Examples
    --------
    "Berserker's" -> {"Berserker"}
    "Berserker's and Valkyrie" -> {"Berserker", "Valkyrie"}
    "Dire and Rabid" -> {"Dire", "Rabid"}
    "Trailblazer's" -> {"Trailblazer"}
    """

    normalized: Set[str] = set()

    # Split composite names ("X and Y") into individual parts
    parts = re.split(r"\sand\s", raw_name)
    for part in parts:
        name = part.strip()
        if not name:
            continue
        # Drop trailing possessive "'s" if present
        if name.endswith("'s"):
            name = name[:-2]
        name = name.strip()
        if name:
            normalized.add(name)

    return normalized


_ITEMSTAT_ATTR_MAP: Dict[str, str] = {
    "Power": "power",
    "Precision": "precision",
    "Toughness": "toughness",
    "Vitality": "vitality",
    "ConditionDamage": "condition_damage",
    "Healing": "healing_power",
    "BoonDuration": "concentration",
    "CritDamage": "ferocity",
    "Expertise": "expertise",
}


@lru_cache(maxsize=1)
def _build_itemstats_index() -> Dict[str, List[Dict[str, Any]]]:
    data_store = GW2DataStore()
    itemstats = data_store.get_itemstats()
    index: Dict[str, List[Dict[str, Any]]] = {}
    if not itemstats:
        return index

    for entry in itemstats:
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        prefixes = _normalize_itemstat_name(name)
        if not prefixes:
            continue
        for prefix in prefixes:
            index.setdefault(prefix, []).append(entry)

    return index


@lru_cache(maxsize=1)
def get_available_prefixes_from_itemstats() -> Set[str]:
    """Return the set of prefix names discoverable from itemstats.json.

    Names are normalised to match PREFIX_REGISTRY keys (e.g. "Berserker's" ->
    "Berserker", "Berserker's and Valkyrie" -> {"Berserker", "Valkyrie"}).
    """

    data_store = GW2DataStore()
    itemstats = data_store.get_itemstats()

    if not itemstats:
        return set()

    available_prefixes: Set[str] = set()
    for entry in itemstats:
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        available_prefixes.update(_normalize_itemstat_name(name))

    return available_prefixes


def filter_prefix_names_by_itemstats(prefix_names: List[str]) -> List[str]:
    """Filter a list of prefix names to those present in GW2 itemstats.

    If itemstats.json is missing/empty or if filtering would remove all
    prefixes, this function returns the original list unchanged and logs a
    warning in the latter case.
    """

    available_prefixes = get_available_prefixes_from_itemstats()
    if not available_prefixes:
        # Pas de données GW2: ne rien filtrer.
        return prefix_names

    filtered = [name for name in prefix_names if name in available_prefixes]

    if filtered:
        return filtered

    logger.warning(
        "Gear prefix filter: none of the requested prefixes are present in "
        "itemstats.json; keeping original list: %s",
        ", ".join(prefix_names),
    )
    return prefix_names


def validate_prefix_registry_against_itemstats() -> None:
    """Validate that all PREFIX_REGISTRY keys exist in GW2 itemstats.

    This helper is *read-only* and does not change any behaviour at runtime.
    It is intended as a diagnostic/validation tool to ensure that our
    PREFIX_REGISTRY only references prefixes that actually exist in GW2
    itemstats.json.

    It will log:
      - a warning if itemstats data is missing or empty
      - a summary of discovered prefixes from itemstats
      - a warning listing any PREFIX_REGISTRY keys not present in itemstats
    """

    available_prefixes = get_available_prefixes_from_itemstats()
    if not available_prefixes:
        logger.warning(
            "Gear prefix validation: itemstats.json is empty or missing; "
            "unable to validate PREFIX_REGISTRY against GW2 data.",
        )
        return

    registry_prefixes = set(PREFIX_REGISTRY.keys())

    missing_in_itemstats = sorted(registry_prefixes - available_prefixes)

    logger.info(
        "Gear prefix validation: %d unique prefixes discovered in itemstats.json",
        len(available_prefixes),
    )

    if not missing_in_itemstats:
        logger.info(
            "Gear prefix validation: all %d prefixes from PREFIX_REGISTRY "
            "are present in itemstats.json",
            len(registry_prefixes),
        )
        return

    logger.warning(
        "Gear prefix validation: %d prefixes from PREFIX_REGISTRY are not "
        "present in itemstats.json: %s",
        len(missing_in_itemstats),
        ", ".join(missing_in_itemstats),
    )


def get_prefix_stats_from_itemstats(prefix_name: str) -> Dict[str, int]:
    base = PREFIX_REGISTRY.get(prefix_name)
    if base is None:
        raise KeyError(f"Unknown gear prefix: {prefix_name!r}")
    index = _build_itemstats_index()
    entries = index.get(prefix_name)
    if not entries:
        return dict(base)
    raw: Dict[str, float] = {k: 0.0 for k in base.keys()}
    for entry in entries:
        attributes = entry.get("attributes") or []
        for attribute in attributes:
            api_attr = attribute.get("attribute")
            if not isinstance(api_attr, str):
                continue
            key = _ITEMSTAT_ATTR_MAP.get(api_attr)
            if not key:
                continue
            val = 0.0
            v = attribute.get("value")
            if isinstance(v, (int, float)):
                val += float(v)
            m = attribute.get("multiplier")
            if isinstance(m, (int, float)):
                val += float(m) * 100.0
            if val <= 0.0:
                continue
            if key not in raw:
                raw[key] = 0.0
            raw[key] += val
    positive = {k: v for k, v in raw.items() if v > 0.0}
    if not positive:
        return dict(base)
    total_data = sum(positive.values())
    total_base = float(sum(base.values())) or 1.0
    result: Dict[str, int] = {}
    for key in base.keys():
        if key in positive:
            share = positive[key] / total_data
            result[key] = int(round(total_base * share))
        else:
            result[key] = 0
    return result
