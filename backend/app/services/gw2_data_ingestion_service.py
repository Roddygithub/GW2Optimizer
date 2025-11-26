"""GW2 Data Ingestion Service
+
+Ce module fournit un squelette pour l'ingestion de données GW2
+(spécialisations, traits, skills, équipements) afin d'alimenter
+les futurs agents data-driven (Team Commander, Build Lab, méta, etc.).
+
+Objectifs V1 (squelette uniquement) :
+  - Centraliser les appels au GW2APIClient pour récupérer les métadonnées.
+  - Exposer quelques méthodes haut niveau (fetch_specializations, fetch_traits,
+    fetch_skills, fetch_item) qui renvoient des vues minifiées réutilisables
+    par les agents.
+  - Préparer le terrain pour une future persistance (DB ou cache) sans
+    l'imposer dès maintenant.
+"""
+
+from typing import Any, Dict, Iterable, List, Optional
+
+from app.core.logging import logger
+from app.services.gw2_api_client import GW2APIClient
+
+
+class GW2DataIngestionService:
+  """Service d'ingestion/agrégation de données GW2.
+
+  V1 : simple façade autour de GW2APIClient avec des helpers de minification.
+  A terme, ce service pourra :
+    - persister les données dans une base locale,
+    - maintenir un cache rafraîchi périodiquement,
+    - exposer des vues agrégées (par profession, par rôle, par meta, etc.).
+  """
+
+  def __init__(self, gw2_client: Optional[GW2APIClient] = None) -> None:
+    self.gw2_client = gw2_client or GW2APIClient()
+
+  def _minify(self, obj: Dict[str, Any], extra_fields: Optional[List[str]] = None) -> Dict[str, Any]:
+    """Conserve uniquement les champs sémantiques utiles.
+
+    - Toujours garder : id, name, description (quand présents).
+    - Ajouter certains champs contextuels (slot, type, profession, elite, etc.).
+    """
+    view: Dict[str, Any] = {}
+
+    for key in ("id", "name", "description"):
+      if key in obj:
+        view[key] = obj[key]
+
+    if extra_fields:
+      for key in extra_fields:
+        if key in obj:
+          view[key] = obj[key]
+
+    return view
+
+  async def fetch_specializations(self, ids: Iterable[int]) -> List[Dict[str, Any]]:
+    """Récupère et minifie une liste de spécialisations GW2."""
+    results: List[Dict[str, Any]] = []
+    for sid in ids:
+      try:
+        spec = await self.gw2_client.get_specialization_details(int(sid))
+      except Exception as e:  # pragma: no cover - robust aux erreurs ponctuelles API
+        logger.error(f"Failed to fetch specialization {sid}: {e}")
+        continue
+      if not spec:
+        continue
+      results.append(self._minify(spec, extra_fields=["profession", "elite"]))
+    return results
+
+  async def fetch_traits(self, ids: Iterable[int]) -> List[Dict[str, Any]]:
+    """Récupère et minifie une liste de traits GW2."""
+    results: List[Dict[str, Any]] = []
+    for tid in ids:
+      try:
+        trait = await self.gw2_client.get_trait_details(int(tid))
+      except Exception as e:  # pragma: no cover
+        logger.error(f"Failed to fetch trait {tid}: {e}")
+        continue
+      if not trait:
+        continue
+      results.append(self._minify(trait, extra_fields=["slot", "tier", "specialization"]))
+    return results
+
+  async def fetch_skills(self, ids: Iterable[int]) -> List[Dict[str, Any]]:
+    """Récupère et minifie une liste de skills GW2."""
+    ids_list = [int(x) for x in ids]
+    if not ids_list:
+      return []
+
+    try:
+      skills = await self.gw2_client.get_skills(ids_list)
+    except Exception as e:  # pragma: no cover
+      logger.error(f"Failed to fetch skills {ids_list}: {e}")
+      return []
+
+    results: List[Dict[str, Any]] = []
+    for s in skills:
+      if not isinstance(s, dict):
+        continue
+      results.append(self._minify(s, extra_fields=["type", "slot", "professions", "flags"]))
+    return results
+
+  async def fetch_item(self, item_id: int) -> Dict[str, Any]:
+    """Récupère et minifie un objet GW2 (arme, armure, etc.).
+
+    V1 : simple proxy; les filtres plus fins (extraction de stats, infusions,
+    runes/sigils intégrés) seront ajoutés ultérieurement.
+    """
+    raw = await self.gw2_client.get_item_details(int(item_id))
+    if not raw:
+      return {}
+    return self._minify(raw, extra_fields=["type", "rarity", "level", "details"])
+
+  async def fetch_all_professions(self) -> List[Dict[str, Any]]:
+    """Récupère et minifie toutes les professions GW2.
+
+    Utilise GW2APIClient.get_all_professions_details puis applique _minify.
+    """
+    try:
+      raw_profs = await self.gw2_client.get_all_professions_details()
+    except Exception as e:  # pragma: no cover
+      logger.error(f"Failed to fetch all professions: {e}")
+      return []
+
+    results: List[Dict[str, Any]] = []
+    for p in raw_profs:
+      if not isinstance(p, dict):
+        continue
+      results.append(self._minify(p, extra_fields=["icon", "icon_big", "profession"]))
+    return results
+
+
+__all__ = ["GW2DataIngestionService"]
