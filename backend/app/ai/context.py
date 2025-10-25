"""
Context Analyzer v4.1.0 - GW2 Meta Awareness

Veille automatique de la méta GW2 depuis sites externes.
Scraping, parsing, normalisation pour ML.

Sources:
    - MetaBattle (WvW, PvE)
    - GuildJen (WvW)
    - SnowCrows (Raids)
    - Hardstuck (Fractals)
    - GW2Mists (WvW)

Note: Version initiale utilise mock data.
      Production: Implémenter vrai scraping avec BeautifulSoup/Scrapy.
"""

import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.core.logging import logger
from app.core.config import settings
from app.learning.data.external import ExternalDataStore, get_external_store


class ContextAnalyzer:
    """
    Analyseur de contexte méta GW2.
    
    Responsibilities:
        - Scrape external sites
        - Parse and normalize data
        - Update meta context
        - Provide ML features
    
    Example:
        ```python
        analyzer = ContextAnalyzer()
        
        # Update context
        await analyzer.update_context()
        
        # Get current meta
        meta = analyzer.get_current_meta()
        print(meta["trending"]["professions"])
        ```
    """
    
    # Sources externes
    SOURCES = {
        "metabattle": "https://metabattle.com/wiki/WvW",
        "guildjen": "https://guildjen.com/",
        "snowcrows": "https://snowcrows.com/",
        "hardstuck": "https://hardstuck.gg/",
        "gw2mists": "https://gw2mists.com/"
    }
    
    def __init__(self, store: Optional[ExternalDataStore] = None):
        """
        Initialise l'analyzer.
        
        Args:
            store: ExternalDataStore instance
        """
        self.store = store or get_external_store()
        self._client: Optional[httpx.AsyncClient] = None
        self._last_update: Optional[datetime] = None
        
        logger.info("ContextAnalyzer initialized")
    
    async def initialize(self) -> None:
        """Initialise le client HTTP"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
    
    async def close(self) -> None:
        """Ferme le client HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def update_context(self, force: bool = False) -> Dict[str, Any]:
        """
        Met à jour le contexte méta.
        
        Args:
            force: Force update même si récent
        
        Returns:
            Updated meta data
        """
        # Check si update nécessaire
        if not force and self._last_update:
            if datetime.utcnow() - self._last_update < timedelta(hours=24):
                logger.info("Meta context is recent, skipping update")
                return self.get_current_meta()
        
        logger.info("🌐 Updating meta context")
        
        await self.initialize()
        
        # Scrape sources (mock pour v4.1.0)
        sources_data = {}
        
        for source_name, source_url in self.SOURCES.items():
            try:
                data = await self._scrape_source(source_name, source_url)
                sources_data[source_name] = data
            except Exception as e:
                logger.warning(f"Failed to scrape {source_name}: {str(e)}")
                sources_data[source_name] = {"error": str(e)}
        
        # Agréger et normaliser
        meta_data = self._aggregate_data(sources_data)
        
        # Sauvegarder
        self.store.save(meta_data)
        
        self._last_update = datetime.utcnow()
        
        logger.info(
            "✅ Meta context updated",
            extra={
                "n_sources": len([s for s in sources_data.values() if "error" not in s]),
                "n_professions": len(meta_data.get("trending", {}).get("professions", []))
            }
        )
        
        return meta_data
    
    async def _scrape_source(
        self,
        source_name: str,
        source_url: str
    ) -> Dict[str, Any]:
        """
        Scrape une source externe.
        
        Note: Version mock pour v4.1.0.
              Production: Implémenter vrai scraping.
        
        Args:
            source_name: Nom de la source
            source_url: URL de la source
        
        Returns:
            Scraped data
        """
        logger.info(f"Scraping {source_name}")
        
        # Mock data pour v4.1.0
        # TODO Production: Implémenter vrai scraping avec BeautifulSoup
        
        mock_data = {
            "metabattle": {
                "trending_professions": [
                    {"name": "Guardian", "popularity": 0.95, "role": "Support"},
                    {"name": "Necromancer", "popularity": 0.90, "role": "DPS"},
                    {"name": "Warrior", "popularity": 0.75, "role": "Tank"}
                ],
                "trending_builds": [
                    {"name": "Firebrand Support", "profession": "Guardian", "mode": "zerg"},
                    {"name": "Scourge DPS", "profession": "Necromancer", "mode": "zerg"}
                ]
            },
            "guildjen": {
                "trending_professions": [
                    {"name": "Guardian", "popularity": 0.92},
                    {"name": "Mesmer", "popularity": 0.80}
                ]
            },
            "snowcrows": {
                "trending_professions": [
                    {"name": "Warrior", "popularity": 0.88, "role": "DPS"},
                    {"name": "Revenant", "popularity": 0.85, "role": "Support"}
                ]
            },
            "hardstuck": {
                "trending_professions": [
                    {"name": "Guardian", "popularity": 0.95},
                    {"name": "Mesmer", "popularity": 0.90}
                ]
            },
            "gw2mists": {
                "trending_professions": [
                    {"name": "Guardian", "popularity": 0.93},
                    {"name": "Necromancer", "popularity": 0.87}
                ]
            }
        }
        
        return mock_data.get(source_name, {})
    
    def _aggregate_data(self, sources_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agrège les données de toutes les sources.
        
        Args:
            sources_data: Données par source
        
        Returns:
            Aggregated meta data
        """
        # Compter popularité par profession
        profession_scores: Dict[str, float] = {}
        profession_counts: Dict[str, int] = {}
        
        for source_name, source_data in sources_data.items():
            if "error" in source_data:
                continue
            
            trending_profs = source_data.get("trending_professions", [])
            
            for prof_data in trending_profs:
                prof_name = prof_data.get("name")
                popularity = prof_data.get("popularity", 0.5)
                
                if prof_name:
                    profession_scores[prof_name] = profession_scores.get(prof_name, 0) + popularity
                    profession_counts[prof_name] = profession_counts.get(prof_name, 0) + 1
        
        # Calculer moyennes
        trending_professions = []
        for prof_name, total_score in profession_scores.items():
            count = profession_counts[prof_name]
            avg_score = total_score / count
            
            trending_professions.append({
                "name": prof_name,
                "popularity": avg_score,
                "n_sources": count,
                "trending_up": avg_score > 0.7
            })
        
        # Trier par popularité
        trending_professions.sort(key=lambda x: x["popularity"], reverse=True)
        
        # Agréger builds
        trending_builds = []
        for source_data in sources_data.values():
            if "error" in source_data:
                continue
            trending_builds.extend(source_data.get("trending_builds", []))
        
        return {
            "sources": sources_data,
            "trending": {
                "professions": trending_professions,
                "builds": trending_builds,
                "by_mode": {
                    "zerg": {
                        "top_professions": ["Guardian", "Necromancer", "Warrior"]
                    },
                    "raid": {
                        "top_professions": ["Guardian", "Warrior", "Revenant"]
                    },
                    "fractals": {
                        "top_professions": ["Guardian", "Mesmer", "Warrior"]
                    }
                }
            }
        }
    
    def get_current_meta(self) -> Dict[str, Any]:
        """
        Récupère la méta actuelle.
        
        Returns:
            Current meta data
        """
        return self.store.load()
    
    def get_trending_professions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Récupère les professions tendances.
        
        Args:
            limit: Nombre max de professions
        
        Returns:
            Liste des professions tendances
        """
        meta = self.get_current_meta()
        trending = meta.get("trending", {})
        professions = trending.get("professions", [])
        
        return professions[:limit]
    
    def should_update(self, max_age_hours: int = 24) -> bool:
        """
        Vérifie si une mise à jour est nécessaire.
        
        Args:
            max_age_hours: Âge max en heures
        
        Returns:
            True si update nécessaire
        """
        meta = self.get_current_meta()
        
        if not meta:
            return True
        
        timestamp_str = meta.get("timestamp")
        if not timestamp_str:
            return True
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = datetime.utcnow() - timestamp.replace(tzinfo=None)
            
            return age > timedelta(hours=max_age_hours)
        except Exception:
            return True


# Singleton instance
_context_analyzer: Optional[ContextAnalyzer] = None


async def get_context_analyzer() -> ContextAnalyzer:
    """
    Récupère ou crée l'instance singleton de l'analyzer.
    
    Returns:
        ContextAnalyzer instance
    """
    global _context_analyzer
    
    if _context_analyzer is None:
        _context_analyzer = ContextAnalyzer()
        await _context_analyzer.initialize()
    
    return _context_analyzer
