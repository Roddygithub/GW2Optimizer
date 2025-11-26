"""CLI utilitaire pour dumper les professions GW2 en JSON local.
+
+Ce script est volontairement minimal et destiné à être lancé manuellement
+par le développeur. Il utilise GW2DataIngestionService pour récupérer
+les professions puis les écrit dans backend/data/gw2/professions.json.
+"""
+
+import asyncio
+import json
+from pathlib import Path
+
+from app.services.gw2_data_ingestion_service import GW2DataIngestionService
+
+
+async def main() -> None:
+    service = GW2DataIngestionService()
+
+    profs = await service.fetch_all_professions()
+
+    base_dir = Path(__file__).resolve().parents[1]
+    out_dir = base_dir / "data" / "gw2"
+    out_dir.mkdir(parents=True, exist_ok=True)
+
+    out_path = out_dir / "professions.json"
+    out_path.write_text(json.dumps(profs, ensure_ascii=False, indent=2), encoding="utf-8")
+
+    print(f"Wrote {len(profs)} professions to {out_path}")
+
+
+if __name__ == "__main__":  # pragma: no cover - script manuel
+    asyncio.run(main())
