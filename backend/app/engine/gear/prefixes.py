from typing import Dict, List, Any


StatDict = Dict[str, int]


PREFIX_REGISTRY: Dict[str, StatDict] = {
    "Berserker": {
        "power": 2800,
        "precision": 2200,
        "ferocity": 1200,
        "toughness": 1000,
        "vitality": 1000,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 0,
        "healing_power": 0,
    },
    "Marauder": {
        "power": 2600,
        "precision": 2300,
        "ferocity": 900,
        "toughness": 1000,
        "vitality": 1400,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 0,
        "healing_power": 0,
    },
    "Dragon": {
        "power": 2700,
        "precision": 2100,
        "ferocity": 900,
        "toughness": 1100,
        "vitality": 1300,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 0,
        "healing_power": 0,
    },
    "Valkyrie": {
        "power": 2600,
        "precision": 1200,
        "ferocity": 1200,
        "toughness": 1000,
        "vitality": 1500,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 0,
        "healing_power": 0,
    },
    "Minstrel": {
        "power": 1300,
        "precision": 1000,
        "ferocity": 0,
        "toughness": 1700,
        "vitality": 1700,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 1400,
        "healing_power": 1200,
    },
    "Harrier": {
        "power": 1600,
        "precision": 1200,
        "ferocity": 0,
        "toughness": 1300,
        "vitality": 1300,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 1500,
        "healing_power": 1700,
    },
    "Cleric": {
        "power": 1500,
        "precision": 900,
        "ferocity": 0,
        "toughness": 1400,
        "vitality": 1500,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 800,
        "healing_power": 2000,
    },
    "Magi": {
        "power": 900,
        "precision": 1200,
        "ferocity": 0,
        "toughness": 1100,
        "vitality": 1700,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 800,
        "healing_power": 1900,
    },
    "Diviner": {
        "power": 1900,
        "precision": 1500,
        "ferocity": 700,
        "toughness": 1200,
        "vitality": 1200,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 1700,
        "healing_power": 500,
    },
    "Soldier": {
        "power": 1900,
        "precision": 1200,
        "ferocity": 400,
        "toughness": 1900,
        "vitality": 1900,
        "condition_damage": 0,
        "expertise": 0,
        "concentration": 800,
        "healing_power": 400,
    },
    "Trailblazer": {
        "power": 900,
        "precision": 900,
        "ferocity": 0,
        "toughness": 1800,
        "vitality": 1800,
        "condition_damage": 1600,
        "expertise": 1300,
        "concentration": 0,
        "healing_power": 0,
    },
    "Dire": {
        "power": 800,
        "precision": 800,
        "ferocity": 0,
        "toughness": 1700,
        "vitality": 1700,
        "condition_damage": 1600,
        "expertise": 1100,
        "concentration": 0,
        "healing_power": 0,
    },
    "Celestial": {
        "power": 900,
        "precision": 900,
        "ferocity": 900,
        "toughness": 900,
        "vitality": 900,
        "condition_damage": 900,
        "expertise": 900,
        "concentration": 900,
        "healing_power": 900,
    },
}


def get_prefix_stats(name: str) -> StatDict:
    stats = PREFIX_REGISTRY.get(name)
    if stats is None:
        raise KeyError(f"Unknown gear prefix: {name!r}")

    # Try to refine stats using GW2 itemstats if available. This keeps
    # PREFIX_REGISTRY as a safe baseline and only adjusts the distribution
    # when real data is present.
    try:
        from app.services.gear_prefix_validator import get_prefix_stats_from_itemstats

        return get_prefix_stats_from_itemstats(name)
    except Exception:
        # On any import or runtime error, fall back to the static registry
        return dict(stats)


def get_all_prefixes() -> Dict[str, StatDict]:
    """Retourne un registre étendu de tous les préfixes connus via itemstats.json.

    Cette fonction lit les données GW2 (itemstats.json) via GW2DataStore pour
    découvrir l'ensemble des préfixes de statistiques disponibles en jeu
    (y compris Ritualist, Grieving, etc.), reconstruit une approximation de
    leurs répartitions de stats et les fusionne avec PREFIX_REGISTRY.

    - Les préfixes déjà présents dans PREFIX_REGISTRY sont toujours inclus.
    - Pour ces préfixes connus, on tente d'utiliser la version dérivée des
      données GW2 (get_prefix_stats_from_itemstats) pour coller aux valeurs
      réelles; en cas d'erreur, on garde les valeurs statiques.
    - Pour les préfixes découverts uniquement dans itemstats.json, on calcule
    une distribution de stats directement à partir des attributs exposés par
    l'API (Power, Precision, Vitality, etc.).
    """

    from app.services.gw2_data_store import GW2DataStore

    try:
        # Import tardif pour éviter toute dépendance circulaire au chargement
        from app.services.gear_prefix_validator import (
            _normalize_itemstat_name,
            _ITEMSTAT_ATTR_MAP,
            get_prefix_stats_from_itemstats,
        )
    except Exception:
        # Si le module de validation n'est pas disponible, on se contente
        # de retourner le registre statique.
        return {name: dict(stats) for name, stats in PREFIX_REGISTRY.items()}

    data_store = GW2DataStore()
    itemstats = data_store.get_itemstats()

    if not itemstats:
        # Pas de données GW2: retourner uniquement le registre statique.
        return {name: dict(stats) for name, stats in PREFIX_REGISTRY.items()}

    # Construire un index prefix -> liste d'entrées itemstats correspondantes
    index: Dict[str, List[Dict[str, Any]]] = {}
    for entry in itemstats:
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        prefixes = _normalize_itemstat_name(name)
        if not prefixes:
            continue
        for prefix in prefixes:
            index.setdefault(prefix, []).append(entry)

    # Base des clés de stats à utiliser pour garantir une structure homogène
    sample_stats = next(iter(PREFIX_REGISTRY.values())) if PREFIX_REGISTRY else {}
    base_keys = list(sample_stats.keys()) if sample_stats else [
        "power",
        "precision",
        "ferocity",
        "toughness",
        "vitality",
        "condition_damage",
        "expertise",
        "concentration",
        "healing_power",
    ]

    merged: Dict[str, StatDict] = {}

    # 1) Préfixes déjà connus: essayer de récupérer une version basée sur les données GW2
    for prefix_name, base in PREFIX_REGISTRY.items():
        try:
            stats_from_data = get_prefix_stats_from_itemstats(prefix_name)
            merged[prefix_name] = stats_from_data
        except Exception:
            # Fallback: garder la version statique
            merged[prefix_name] = dict(base)

    # 2) Préfixes découverts uniquement via itemstats.json
    for prefix_name, entries in index.items():
        if prefix_name in merged:
            continue

        # Agréger les attributs bruts pour ce préfixe
        raw: Dict[str, float] = {k: 0.0 for k in base_keys}
        for entry in entries:
            attributes = entry.get("attributes") or []
            if not isinstance(attributes, list):
                continue
            for attribute in attributes:
                if not isinstance(attribute, dict):
                    continue
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
                    # Même logique que get_prefix_stats_from_itemstats: multiplier
                    # converti grossièrement en "valeur" supplémentaire.
                    val += float(m) * 100.0
                if val <= 0.0:
                    continue
                if key not in raw:
                    raw[key] = 0.0
                raw[key] += val

        positive = {k: v for k, v in raw.items() if v > 0.0}
        if not positive:
            continue

        # Construire un StatDict entier à partir des valeurs agrégées
        stats_dict: StatDict = {k: 0 for k in base_keys}
        for k, v in positive.items():
            stats_dict[k] = int(round(v))

        merged[prefix_name] = stats_dict

    return merged
