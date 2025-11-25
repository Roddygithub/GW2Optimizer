"""
GW2 API Client

Client pour l'API officielle de Guild Wars 2.
Permet l'importation automatique des données (professions, skills, traits, items).

Documentation API: https://wiki.guildwars2.com/wiki/API:Main
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime, timedelta

import httpx
from app.core.logging import logger


class Gw2ApiError(Exception):
    pass


class GW2APIClient:
    """
    Client pour l'API officielle Guild Wars 2.

    Endpoints supportés:
    - /v2/professions: Professions et leurs mécaniques
    - /v2/skills: Compétences
    - /v2/traits: Traits
    - /v2/specializations: Spécialisations
    - /v2/items: Items et équipement
    - /v2/itemstats: Statistiques d'items

    Example:
        ```python
        client = GW2APIClient()
        professions = await client.get_professions()
        skills = await client.get_skills([12345, 67890])
        ```
    """

    BASE_URL = "https://api.guildwars2.com"
    API_VERSION = "v2"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialise le client API GW2.

        Args:
            api_key: Clé API GW2 (optionnel, requis pour certains endpoints)
            timeout: Timeout des requêtes en secondes
            max_retries: Nombre maximum de tentatives
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(hours=24)

        # Headers par défaut
        self.headers = {"User-Agent": "GW2Optimizer/1.1.0", "Accept": "application/json"}

        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Any:
        """
        Effectue une requête à l'API GW2.

        Args:
            endpoint: Endpoint de l'API (ex: "/v2/professions")
            params: Paramètres de requête
            use_cache: Utiliser le cache si disponible

        Returns:
            Réponse JSON de l'API

        Raises:
            httpx.HTTPError: En cas d'erreur HTTP
        """
        url = f"{self.BASE_URL}/{self.API_VERSION}/{endpoint}"
        cache_key = f"{url}:{str(params)}"

        # Vérifier le cache
        if use_cache and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.utcnow() - cached_time < self._cache_ttl:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_data

        # Effectuer la requête avec retry
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()

                    # Mettre en cache
                    if use_cache:
                        self._cache[cache_key] = (data, datetime.utcnow())

                    logger.info(f"Successfully fetched {endpoint}")
                    return data

            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {endpoint}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {endpoint} after {self.max_retries} attempts")
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

    # ==================== Professions ====================

    async def get_professions(self) -> List[str]:
        """
        Récupère la liste des IDs de professions.

        Returns:
            Liste des IDs de professions
        """
        return await self._request("professions")

    async def get_profession(self, profession_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une profession.

        Args:
            profession_id: ID de la profession (ex: "Guardian")

        Returns:
            Détails de la profession
        """
        return await self._request(f"professions/{profession_id}")

    async def get_profession_with_skills(self, profession_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une profession avec les champs étendus.

        Utilise la version "latest" de l'API pour exposer notamment
        ``skills_by_palette`` qui permet de résoudre les palette IDs des
        templates de build en IDs de compétences GW2.
        """

        params = {"v": "latest"}
        return await self._request(f"professions/{profession_id}", params=params)

    async def get_all_professions_details(self) -> List[Dict[str, Any]]:
        """
        Récupère les détails de toutes les professions.

        Returns:
            Liste des détails de professions
        """
        profession_ids = await self.get_professions()

        tasks = [self.get_profession(prof_id) for prof_id in profession_ids]
        professions = await asyncio.gather(*tasks)

        return professions

    # ==================== Skills ====================

    async def get_skills(self, skill_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les compétences.

        Args:
            skill_ids: Liste des IDs de compétences (optionnel)

        Returns:
            Liste des compétences
        """
        if skill_ids:
            params = {"ids": ",".join(map(str, skill_ids))}
            return await self._request("skills", params=params)
        else:
            # Récupérer tous les IDs puis les détails
            all_ids = await self._request("skills")
            # Limiter à 200 IDs par requête (limite API)
            return await self._get_paginated("skills", all_ids, page_size=200)

    async def get_skill(self, skill_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une compétence.

        Args:
            skill_id: ID de la compétence

        Returns:
            Détails de la compétence
        """
        return await self._request(f"skills/{skill_id}")

    async def get_skill_details(self, skill_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.get_skill(skill_id)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                logger.warning(f"Skill not found in GW2 API: {skill_id}")
                return None
            logger.error(f"GW2 API returned error for skill {skill_id}: {exc}")
            raise Gw2ApiError(f"Failed to fetch skill {skill_id}") from exc
        except httpx.HTTPError as exc:
            logger.error(f"GW2 API request failed for skill {skill_id}: {exc}")
            raise Gw2ApiError(f"Failed to fetch skill {skill_id}") from exc

    # ==================== Traits ====================

    async def get_traits(self, trait_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les traits.

        Args:
            trait_ids: Liste des IDs de traits (optionnel)

        Returns:
            Liste des traits
        """
        if trait_ids:
            params = {"ids": ",".join(map(str, trait_ids))}
            return await self._request("traits", params=params)
        else:
            all_ids = await self._request("traits")
            return await self._get_paginated("traits", all_ids, page_size=200)

    async def get_trait(self, trait_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un trait.

        Args:
            trait_id: ID du trait

        Returns:
            Détails du trait
        """
        return await self._request(f"traits/{trait_id}")

    async def get_trait_details(self, trait_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'un trait avec gestion des erreurs.

        Renvoie None si le trait n'existe pas (404), sinon lève Gw2ApiError
        pour les autres erreurs réseau.
        """
        try:
            return await self.get_trait(trait_id)
        except httpx.HTTPStatusError as exc:  # type: ignore[reportGeneralTypeIssues]
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                logger.warning(f"Trait not found in GW2 API: {trait_id}")
                return None
            logger.error(f"GW2 API returned error for trait {trait_id}: {exc}")
            raise Gw2ApiError(f"Failed to fetch trait {trait_id}") from exc
        except httpx.HTTPError as exc:  # type: ignore[reportGeneralTypeIssues]
            logger.error(f"GW2 API request failed for trait {trait_id}: {exc}")
            raise Gw2ApiError(f"Failed to fetch trait {trait_id}") from exc

    # ==================== Specializations ====================

    async def get_specializations(self, spec_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les spécialisations.

        Args:
            spec_ids: Liste des IDs de spécialisations (optionnel)

        Returns:
            Liste des spécialisations
        """
        if spec_ids:
            params = {"ids": ",".join(map(str, spec_ids))}
            return await self._request("specializations", params=params)
        else:
            all_ids = await self._request("specializations")
            return await self._get_paginated("specializations", all_ids, page_size=200)

    async def get_specialization(self, spec_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une spécialisation.

        Args:
            spec_id: ID de la spécialisation

        Returns:
            Détails de la spécialisation
        """
        return await self._request(f"specializations/{spec_id}")

    async def get_specialization_details(self, spec_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'une spécialisation avec gestion des erreurs.

        Renvoie None si la spécialisation n'existe pas (404), sinon lève
        Gw2ApiError pour les autres erreurs réseau.
        """
        try:
            return await self.get_specialization(spec_id)
        except httpx.HTTPStatusError as exc:  # type: ignore[reportGeneralTypeIssues]
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                logger.warning(f"Specialization not found in GW2 API: {spec_id}")
                return None
            logger.error(f"GW2 API returned error for specialization {spec_id}: {exc}")
            raise Gw2ApiError(f"Failed to fetch specialization {spec_id}") from exc
        except httpx.HTTPError as exc:  # type: ignore[reportGeneralTypeIssues]
            logger.error(f"GW2 API request failed for specialization {spec_id}: {exc}")
            raise Gw2ApiError(f"Failed to fetch specialization {spec_id}") from exc

    # ==================== Items ====================

    async def get_items(self, item_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les items.

        Args:
            item_ids: Liste des IDs d'items (optionnel)

        Returns:
            Liste des items
        """
        if item_ids:
            params = {"ids": ",".join(map(str, item_ids))}
            return await self._request("items", params=params)
        else:
            # Note: L'API items a des milliers d'entrées, ne pas tout charger
            logger.warning("Fetching all items is not recommended. Use specific IDs.")
            return []

    async def get_item(self, item_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un item.

        Args:
            item_id: ID de l'item

        Returns:
            Détails de l'item
        """
        return await self._request(f"items/{item_id}")

    async def get_itemstats(self, stat_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques d'items.

        Args:
            stat_ids: Liste des IDs de stats (optionnel)

        Returns:
            Liste des statistiques
        """
        if stat_ids:
            params = {"ids": ",".join(map(str, stat_ids))}
            return await self._request("itemstats", params=params)
        else:
            all_ids = await self._request("itemstats")
            return await self._get_paginated("itemstats", all_ids, page_size=200)

    # ==================== Helpers ====================

    async def _get_paginated(self, endpoint: str, all_ids: List[int], page_size: int = 200) -> List[Dict[str, Any]]:
        """
        Récupère des données paginées.

        Args:
            endpoint: Endpoint de l'API
            all_ids: Liste de tous les IDs
            page_size: Taille de page

        Returns:
            Liste complète des données
        """
        results = []

        for i in range(0, len(all_ids), page_size):
            batch_ids = all_ids[i : i + page_size]
            params = {"ids": ",".join(map(str, batch_ids))}

            try:
                batch_data = await self._request(endpoint, params=params)
                results.extend(batch_data)
            except Exception as e:
                logger.error(f"Failed to fetch batch {i}-{i + page_size}: {e}")

        return results

    async def import_all_game_data(self) -> Dict[str, Any]:
        """
        Importe toutes les données de jeu essentielles.

        Returns:
            Dictionnaire contenant toutes les données importées
        """
        logger.info("Starting full game data import from GW2 API")

        try:
            # Importer en parallèle
            professions, specializations, traits = await asyncio.gather(
                self.get_all_professions_details(),
                self.get_specializations(),
                self.get_traits(),
                return_exceptions=True,
            )

            # Vérifier les erreurs
            if isinstance(professions, Exception):
                logger.error(f"Failed to import professions: {professions}")
                professions = []

            if isinstance(specializations, Exception):
                logger.error(f"Failed to import specializations: {specializations}")
                specializations = []

            if isinstance(traits, Exception):
                logger.error(f"Failed to import traits: {traits}")
                traits = []

            data = {
                "professions": professions,
                "specializations": specializations,
                "traits": traits,
                "import_timestamp": datetime.utcnow().isoformat(),
                "success": True,
            }

            logger.info(
                f"Game data import completed: "
                f"{len(professions)} professions, "
                f"{len(specializations)} specializations, "
                f"{len(traits)} traits"
            )

            return data

        except Exception as e:
            logger.error(f"Failed to import game data: {e}", exc_info=True)
            return {
                "professions": [],
                "specializations": [],
                "traits": [],
                "import_timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e),
            }

    def clear_cache(self) -> None:
        """Vide le cache."""
        self._cache.clear()
        logger.info("API cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache.

        Returns:
            Statistiques du cache
        """
        return {"cache_size": len(self._cache), "cache_ttl_hours": self._cache_ttl.total_seconds() / 3600}
