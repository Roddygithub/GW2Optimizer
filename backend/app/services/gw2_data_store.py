from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import logger


class GW2DataStore:
    def __init__(self, data_dir: Optional[Path] = None) -> None:
        if data_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
            data_dir = base_dir / "data" / "gw2"
        self.data_dir = data_dir

        self._skills: Optional[List[Dict[str, Any]]] = None
        self._items: Optional[List[Dict[str, Any]]] = None
        self._upgrade_components: Optional[List[Dict[str, Any]]] = None
        self._itemstats: Optional[List[Dict[str, Any]]] = None
        self._professions: Optional[List[Dict[str, Any]]] = None
        self._specializations: Optional[List[Dict[str, Any]]] = None
        self._traits: Optional[List[Dict[str, Any]]] = None

    def _load_list(self, filename: str) -> List[Dict[str, Any]]:
        path = self.data_dir / f"{filename}.json"
        if not path.exists():
            logger.warning("GW2DataStore: file not found: %s", path)
            return []

        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error("GW2DataStore: failed to load %s: %s", path, exc)
            return []

        if isinstance(data, list):
            return data

        logger.warning("GW2DataStore: file %s does not contain a list", path)
        return []

    def get_skills(self) -> List[Dict[str, Any]]:
        if self._skills is None:
            self._skills = self._load_list("skills")
        return self._skills

    def get_items(self) -> List[Dict[str, Any]]:
        if self._items is None:
            self._items = self._load_list("items")
        return self._items

    def get_upgrade_components(self) -> List[Dict[str, Any]]:
        if self._upgrade_components is None:
            components = self._load_list("upgrade_components")
            if not components:
                items = self.get_items()
                components = [it for it in items if it.get("type") == "UpgradeComponent"]
                if components:
                    logger.info("GW2DataStore: derived upgrade_components from items.json")
            self._upgrade_components = components
        return self._upgrade_components

    def get_itemstats(self) -> List[Dict[str, Any]]:
        if self._itemstats is None:
            self._itemstats = self._load_list("itemstats")
        return self._itemstats

    def get_professions(self) -> List[Dict[str, Any]]:
        if self._professions is None:
            self._professions = self._load_list("professions")
        return self._professions

    def get_specializations(self) -> List[Dict[str, Any]]:
        if self._specializations is None:
            self._specializations = self._load_list("specializations")
        return self._specializations

    def get_traits(self) -> List[Dict[str, Any]]:
        if self._traits is None:
            self._traits = self._load_list("traits")
        return self._traits

    def get_runes(self) -> List[Dict[str, Any]]:
        components = self.get_upgrade_components()
        runes: List[Dict[str, Any]] = []
        for c in components:
            name = c.get("name")
            if not isinstance(name, str):
                continue
            if "Rune of " in name:
                runes.append(c)
        return runes

    def get_sigils(self) -> List[Dict[str, Any]]:
        components = self.get_upgrade_components()
        sigils: List[Dict[str, Any]] = []
        for c in components:
            name = c.get("name")
            if not isinstance(name, str):
                continue
            if "Sigil of " in name:
                sigils.append(c)
        return sigils
