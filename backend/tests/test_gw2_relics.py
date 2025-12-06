import json
from pathlib import Path

import pytest

from app.services.gw2_data_store import GW2DataStore
from app.agents.build_equipment_optimizer import BuildEquipmentOptimizer


def test_gw2_data_store_relics_contains_key_wvw_relics():
    """GW2DataStore.get_relics should expose key WvW relics used by the optimizer.

    This validates that our local GW2 dump is up-to-date enough for Fireworks/Flock/Monk/
    Herald/Scourge/Centaur, which are the core WvW relics modeled in RELIC_REGISTRY.
    """

    store = GW2DataStore()
    relics = store.get_relics()

    assert relics, "Expected at least one relic in GW2 data; got empty list. Check data/gw2/items.json."

    names = {r.get("name") for r in relics if isinstance(r.get("name"), str)}
    expected = {
        "Relic of Fireworks",
        "Relic of the Flock",
        "Relic of the Monk",
        "Relic of the Herald",
        "Relic of the Scourge",
        "Relic of the Centaur",
    }

    missing = sorted(expected - names)
    assert not missing, f"Missing expected relics in GW2 data: {missing}"


def test_gw2_data_store_get_relics_falls_back_to_items_when_no_relics_json(tmp_path: Path):
    """get_relics should derive relics from items.json when relics.json is absent."""

    data_dir = tmp_path / "gw2"
    data_dir.mkdir()

    items = [
        {
            "name": "Relic of Fireworks",
            "type": "Relic",
        },
        {
            "name": "Some Weapon",
            "type": "Weapon",
        },
    ]
    (data_dir / "items.json").write_text(json.dumps(items), encoding="utf-8")

    store = GW2DataStore(data_dir=data_dir)
    relics = store.get_relics()

    assert len(relics) == 1
    assert relics[0]["name"] == "Relic of Fireworks"


def test_normalize_relic_name_from_api_matches_registry_keys():
    """_normalize_relic_name_from_api should produce keys compatible with RELIC_REGISTRY."""

    optimizer = BuildEquipmentOptimizer()
    normalize = optimizer._normalize_relic_name_from_api

    assert normalize("Relic of Fireworks") == "Fireworks"
    assert normalize("Relic of the Monk") == "Monk"
    assert normalize("Relic of the Herald") == "Herald"
    assert normalize("Relic of the Flock") == "Flock"
    assert normalize("Relic of the Centaur") == "Centaur"
    assert normalize("Relic of the Scourge") == "Scourge"


@pytest.mark.parametrize(
    "role, allowed",
    [
        ("dps", {"Fireworks"}),
        ("heal", {"Flock", "Monk"}),
        ("boon", {"Herald", "Monk", "Flock"}),
        ("tank", {"Centaur", "Scourge"}),
        ("support", {"Herald", "Flock", "Monk"}),
    ],
)
def test_get_relic_for_role_uses_known_wvw_relics(role: str, allowed: set[str]):
    """BuildEquipmentOptimizer.get_relic_for_role should pick a relic from RELIC_REGISTRY.

    We only assert membership in an allowed set per role to keep the test robust if
    data/gw2/items.json evolves (e.g. one of the preferred relics is temporarily
    missing in the dump).
    """

    optimizer = BuildEquipmentOptimizer()
    relic = optimizer.get_relic_for_role(role)

    if relic is None:
        pytest.skip("No matching relics found in local GW2 data; update data/gw2/items.json.")

    assert relic in allowed
