"""
External Data Store v4.1.0 - Meta Data Storage

Stockage local des données de méta GW2 scrappées depuis sites externes.
Format JSON versionné pour historisation et ML features.

Sources:
    - MetaBattle
    - GuildJen
    - SnowCrows
    - Hardstuck
    - GW2Mists

Storage Format:
    {
        "version": "4.1.0",
        "timestamp": "2025-10-24T10:00:00Z",
        "sources": {
            "metabattle": {...},
            "guildjen": {...},
            ...
        },
        "trending": {
            "professions": [...],
            "builds": [...],
            "by_mode": {...}
        }
    }
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from app.core.logging import logger
from app.core.config import settings


class ExternalDataStore:
    """
    Stockage des données de méta externe.
    
    Responsibilities:
        - Save scraped meta data
        - Load historical data
        - Version management
        - ML feature extraction
    
    Example:
        ```python
        store = ExternalDataStore()
        
        # Save meta data
        store.save({
            "trending": {
                "professions": ["Guardian", "Necromancer"],
                "builds": [...]
            }
        })
        
        # Load current meta
        meta = store.load()
        
        # Get ML features
        features = store.get_features_for_ml()
        ```
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialise le store.
        
        Args:
            storage_dir: Dossier de stockage
        """
        self.storage_dir = storage_dir or str(
            Path(settings.LEARNING_DATA_DIR) / "external"
        )
        
        # Créer dossiers
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        
        # Fichiers
        self.current_file = Path(self.storage_dir) / "current_meta.json"
        self.history_dir = Path(self.storage_dir) / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "ExternalDataStore initialized",
            extra={"storage_dir": self.storage_dir}
        )
    
    def save(self, data: Dict[str, Any]) -> str:
        """
        Sauvegarde les données de méta.
        
        Args:
            data: Meta data à sauvegarder
        
        Returns:
            Path du fichier sauvegardé
        """
        # Ajouter métadonnées
        meta_data = {
            "version": "4.1.0",
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        
        # Sauvegarder current
        with open(self.current_file, 'w') as f:
            json.dump(meta_data, f, indent=2)
        
        # Sauvegarder dans historique
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        history_file = self.history_dir / f"meta_{timestamp}.json"
        
        with open(history_file, 'w') as f:
            json.dump(meta_data, f, indent=2)
        
        logger.info(
            "Meta data saved",
            extra={
                "timestamp": timestamp,
                "sources": list(data.get("sources", {}).keys())
            }
        )
        
        return str(self.current_file)
    
    def load(self, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Charge les données de méta.
        
        Args:
            version: Version spécifique (timestamp) ou None pour current
        
        Returns:
            Meta data
        """
        if version:
            # Charger version historique
            history_file = self.history_dir / f"meta_{version}.json"
            if not history_file.exists():
                logger.warning(f"Version not found: {version}")
                return {}
            
            with open(history_file, 'r') as f:
                return json.load(f)
        
        # Charger current
        if not self.current_file.exists():
            logger.warning("No current meta data found")
            return {}
        
        with open(self.current_file, 'r') as f:
            return json.load(f)
    
    def get_features_for_ml(self) -> pd.DataFrame:
        """
        Extrait les features pour ML depuis la méta actuelle.
        
        Returns:
            DataFrame avec features
        """
        meta = self.load()
        
        if not meta:
            return pd.DataFrame()
        
        # Extraire trending professions
        trending = meta.get("trending", {})
        professions = trending.get("professions", [])
        
        # Créer features
        features = []
        
        for prof_data in professions:
            if isinstance(prof_data, dict):
                features.append({
                    "profession": prof_data.get("name"),
                    "popularity": prof_data.get("popularity", 0),
                    "win_rate": prof_data.get("win_rate", 0),
                    "trending_up": prof_data.get("trending_up", False)
                })
            elif isinstance(prof_data, str):
                # Simple list of names
                features.append({
                    "profession": prof_data,
                    "popularity": 1.0,
                    "win_rate": 0.5,
                    "trending_up": True
                })
        
        return pd.DataFrame(features)
    
    def get_trending_by_mode(self, game_mode: str) -> Dict[str, Any]:
        """
        Récupère les tendances pour un mode de jeu spécifique.
        
        Args:
            game_mode: Mode de jeu (zerg, raid, fractals, etc.)
        
        Returns:
            Trending data pour ce mode
        """
        meta = self.load()
        
        trending = meta.get("trending", {})
        by_mode = trending.get("by_mode", {})
        
        return by_mode.get(game_mode, {})
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des métas.
        
        Args:
            limit: Nombre max de versions
        
        Returns:
            Liste des métas historiques
        """
        history_files = sorted(
            self.history_dir.glob("meta_*.json"),
            reverse=True
        )[:limit]
        
        history = []
        for file in history_files:
            with open(file, 'r') as f:
                history.append(json.load(f))
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les données stockées.
        
        Returns:
            Statistics dict
        """
        meta = self.load()
        history = self.get_history(limit=100)
        
        return {
            "current_version": meta.get("version"),
            "last_update": meta.get("timestamp"),
            "n_sources": len(meta.get("sources", {})),
            "n_trending_professions": len(meta.get("trending", {}).get("professions", [])),
            "n_trending_builds": len(meta.get("trending", {}).get("builds", [])),
            "n_historical_versions": len(history),
            "sources": list(meta.get("sources", {}).keys())
        }


# Singleton instance
_external_store: Optional[ExternalDataStore] = None


def get_external_store() -> ExternalDataStore:
    """
    Récupère ou crée l'instance singleton du store.
    
    Returns:
        ExternalDataStore instance
    """
    global _external_store
    
    if _external_store is None:
        _external_store = ExternalDataStore()
    
    return _external_store
