from app.engine.gear.prefixes import PREFIX_REGISTRY, get_prefix_stats


def test_prefix_registry_contains_core_prefixes() -> None:
    for name in ["Berserker", "Marauder", "Minstrel", "Diviner", "Soldier", "Celestial"]:
        assert name in PREFIX_REGISTRY
        stats = get_prefix_stats(name)
        # Toutes les entrées doivent exposer les mêmes clés de stats
        for key in [
            "power",
            "precision",
            "ferocity",
            "toughness",
            "vitality",
            "condition_damage",
            "expertise",
            "concentration",
            "healing_power",
        ]:
            assert key in stats


def test_minstrel_is_much_tankier_and_more_healy_than_berserker() -> None:
    berserker = get_prefix_stats("Berserker")
    minstrel = get_prefix_stats("Minstrel")

    assert minstrel["toughness"] > berserker["toughness"]
    assert minstrel["vitality"] > berserker["vitality"]
    assert minstrel["healing_power"] > berserker["healing_power"]
    assert berserker["ferocity"] > minstrel["ferocity"]


def test_diviner_has_high_concentration() -> None:
    berserker = get_prefix_stats("Berserker")
    diviner = get_prefix_stats("Diviner")

    assert diviner["concentration"] > berserker["concentration"]
    assert diviner["power"] >= 1800


def test_celestial_has_mixed_offensive_and_defensive_stats() -> None:
    celestial = get_prefix_stats("Celestial")

    # Celestial doit apporter des stats dans plusieurs domaines
    offensive = celestial["power"] + celestial["precision"] + celestial["condition_damage"]
    defensive = celestial["toughness"] + celestial["vitality"]
    support = celestial["healing_power"] + celestial["concentration"] + celestial["expertise"]

    assert offensive > 0
    assert defensive > 0
    assert support > 0
