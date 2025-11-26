from app.engine.gear.prefixes import PREFIX_REGISTRY, get_prefix_stats


def test_prefix_registry_contains_core_prefixes() -> None:
    for name in ["Berserker", "Marauder", "Minstrel", "Diviner", "Soldier"]:
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
