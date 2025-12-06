"""Full GW2 game data import script.

This script performs a controlled full pass over key GW2 API endpoints
and writes the results to JSON files under backend/data/gw2/.

It is designed to be run automatically (e.g. via cron or a scheduler).
It uses /v2/build to detect whether the game build has changed and will
skip the import if there is no new build.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.gw2_api_client import GW2APIClient


DATA_SUBDIR = "data/gw2"


async def full_import_if_needed() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / DATA_SUBDIR
    data_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = data_dir / "metadata.json"
    last_build_id: int | None = None
    if metadata_path.exists():
        try:
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
            if isinstance(meta, dict) and isinstance(meta.get("build_id"), int):
                last_build_id = meta["build_id"]
        except Exception:
            # Ignore malformed metadata and force a fresh import
            last_build_id = None

    client = GW2APIClient()

    current_build_id = await client.get_build_id()

    if last_build_id is not None and current_build_id == last_build_id:
        print(f"GW2 full import: up to date (build_id={current_build_id}), nothing to do.")
        return

    print(f"GW2 full import: new build detected (old={last_build_id}, new={current_build_id}), importing...")

    game_data = await client.import_all_game_data()
    # import_all_game_data currently returns professions, specializations, traits
    professions = game_data.get("professions", [])
    specializations = game_data.get("specializations", [])
    traits = game_data.get("traits", [])

    # Fetch all skills, items and itemstats (paginated internally by the client)
    skills_result, items_result, itemstats_result = await asyncio.gather(
        client.get_skills(),
        client.get_all_items(),
        client.get_itemstats(),
        return_exceptions=True,
    )

    # Handle potential exceptions from gather
    skills = skills_result if not isinstance(skills_result, Exception) else []
    items = items_result if not isinstance(items_result, Exception) else []
    itemstats = itemstats_result if not isinstance(itemstats_result, Exception) else []

    # Derive upgrade components from items (type == "UpgradeComponent")
    if items:
        upgrade_components = [it for it in items if it.get("type") == "UpgradeComponent"]
        relics = [it for it in items if it.get("type") == "Relic"]
    else:
        upgrade_components = []
        relics = []

    # Log any failures
    if isinstance(skills_result, Exception):
        print(f"⚠️ Failed to fetch skills: {skills_result}")
    if isinstance(items_result, Exception):
        print(f"⚠️ Failed to fetch items: {items_result}")
    if isinstance(itemstats_result, Exception):
        print(f"⚠️ Failed to fetch itemstats: {itemstats_result}")

    # Dump to JSON files
    (data_dir / "professions.json").write_text(
        json.dumps(professions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "specializations.json").write_text(
        json.dumps(specializations, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "traits.json").write_text(
        json.dumps(traits, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "skills.json").write_text(
        json.dumps(skills, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "items.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "upgrade_components.json").write_text(
        json.dumps(upgrade_components, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "relics.json").write_text(
        json.dumps(relics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (data_dir / "itemstats.json").write_text(
        json.dumps(itemstats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Update metadata with new build id and timestamp
    metadata = {
        "build_id": current_build_id,
        "import_timestamp": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "professions": len(professions),
            "specializations": len(specializations),
            "traits": len(traits),
            "skills": len(skills),
            "items": len(items),
            "upgrade_components": len(upgrade_components),
            "relics": len(relics),
            "itemstats": len(itemstats),
        },
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "GW2 full import completed:",
        f"build_id={current_build_id}",
        f"professions={len(professions)}",
        f"specializations={len(specializations)}",
        f"traits={len(traits)}",
        f"skills={len(skills)}",
        f"items={len(items)}",
        f"upgrade_components={len(upgrade_components)}",
        f"relics={len(relics)}",
        f"itemstats={len(itemstats)}",
    )


async def main() -> None:  # pragma: no cover - integration script
    await full_import_if_needed()


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    asyncio.run(main())
