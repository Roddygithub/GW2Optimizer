from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json


@dataclass(frozen=True)
class MetaBuild:
    """Canonical representation of a meta build template."""

    id: str
    name: str
    profession: str
    specialization: str
    role: str
    game_mode: str
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    chat_code: Optional[str] = None
    stats_text: Optional[str] = None
    runes_text: Optional[str] = None


META_BUILD_REGISTRY: Dict[str, MetaBuild] = {}


def list_meta_builds() -> List[MetaBuild]:
    """Return all registered meta builds."""

    return list(META_BUILD_REGISTRY.values())


def query_meta_builds(
    *,
    profession: Optional[str] = None,
    specialization: Optional[str] = None,
    role: Optional[str] = None,
    game_mode: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> List[MetaBuild]:
    """Filter meta builds by simple fields. Case-insensitive, all filters optional."""

    results: List[MetaBuild] = []

    for meta in META_BUILD_REGISTRY.values():
        if profession and meta.profession.lower() != profession.lower():
            continue
        if specialization and meta.specialization.lower() != specialization.lower():
            continue
        if role and meta.role.lower() != role.lower():
            continue
        if game_mode and meta.game_mode.lower() != game_mode.lower():
            continue
        if tags:
            meta_tags = {t.lower() for t in meta.tags}
            query_tags = {t.lower() for t in tags}
            if not query_tags.issubset(meta_tags):
                continue
        results.append(meta)

    return results


def find_closest_meta_build(
    *,
    profession: Optional[str] = None,
    specialization: Optional[str] = None,
    role: Optional[str] = None,
    game_mode: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[MetaBuild]:
    """Best-effort lookup for a single meta build matching simple criteria.

    The current implementation relies only on exact filters and returns the first
    matching entry, or None if the registry is empty or no match exists.
    """

    candidates = query_meta_builds(
        profession=profession,
        specialization=specialization,
        role=role,
        game_mode=game_mode,
        tags=tags,
    )

    if not candidates:
        return None

    return candidates[0]


def find_meta_build_by_chat_code(chat_code: str) -> Optional[MetaBuild]:
    if not chat_code:
        return None
    target = chat_code.strip()
    if not target:
        return None
    for meta in META_BUILD_REGISTRY.values():
        if not meta.chat_code:
            continue
        if meta.chat_code.strip() == target:
            return meta
    return None


def _load_meta_builds_from_payload(payload: Any) -> int:
    META_BUILD_REGISTRY.clear()

    items: List[Dict[str, Any]]
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("builds"), list):
        items = payload["builds"]
    else:
        return 0

    count = 0
    for raw in items:
        if not isinstance(raw, dict):
            continue
        mid = raw.get("id")
        name = raw.get("name")
        profession = raw.get("profession")
        specialization = raw.get("specialization")
        role = raw.get("role")
        game_mode = raw.get("game_mode")
        if not all(isinstance(v, str) and v for v in [mid, name, profession, specialization, role, game_mode]):
            continue
        tags = raw.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        meta = MetaBuild(
            id=mid,
            name=name,
            profession=profession,
            specialization=specialization,
            role=role,
            game_mode=game_mode,
            source=raw.get("source"),
            tags=list(tags),
            notes=raw.get("notes"),
            chat_code=raw.get("chat_code"),
            stats_text=raw.get("stats_text"),
            runes_text=raw.get("runes_text"),
        )
        META_BUILD_REGISTRY[meta.id] = meta
        count += 1
    return count


def load_meta_builds_from_json(path: Union[str, Path]) -> int:
    p = Path(path)
    if not p.is_file():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return _load_meta_builds_from_payload(data)
