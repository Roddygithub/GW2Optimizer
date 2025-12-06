import json
from pathlib import Path

import pytest

from app.core.config import settings
from app.services.learning.pipeline import LearningPipeline
from app.models.learning import FineTuningConfig, StorageConfig


pytestmark = pytest.mark.asyncio


async def test_ingest_meta_builds_is_idempotent(tmp_path, monkeypatch):
    # Isoler le stockage de training_data pour ce test afin d'éviter
    # toute interférence avec des données persistantes ou d'autres tests.
    test_db_path = tmp_path / "local_db" / "gw2optimizer.db"
    monkeypatch.setattr(settings, "DATABASE_PATH", str(test_db_path), raising=False)

    base_dir = Path(__file__).resolve().parent.parent
    meta_dir = base_dir / "data" / "learning" / "external"
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / "meta_builds_wvw.json"

    payload = {
        "builds": [
            {
                "id": "test-meta-1",
                "name": "Test Meta Build 1",
                "profession": "Guardian",
                "specialization": "Firebrand",
                "role": "support",
                "game_mode": "wvw_zerg",
                "source": "test",
                "tags": ["wvw", "zerg"],
            },
            {
                "id": "test-meta-2",
                "name": "Test Meta Build 2",
                "profession": "Necromancer",
                "specialization": "Scourge",
                "role": "dps",
                "game_mode": "wvw_zerg",
                "source": "test",
                "tags": ["wvw", "zerg"],
            },
        ]
    }
    meta_path.write_text(json.dumps(payload), encoding="utf-8")

    pipeline = LearningPipeline(
        finetuning_config=FineTuningConfig(),
        storage_config=StorageConfig(),
    )

    before = await pipeline.collector.get_all_datapoints()
    before_len = len(before)

    added_first = await pipeline.ingest_meta_builds()
    after_first = await pipeline.collector.get_all_datapoints()
    after_first_len = len(after_first)

    assert added_first == 2
    assert after_first_len == before_len + 2

    added_second = await pipeline.ingest_meta_builds()
    after_second = await pipeline.collector.get_all_datapoints()

    assert added_second == 0
    assert len(after_second) == after_first_len
