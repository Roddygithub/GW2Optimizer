"""
Script d'initialisation de la base de données pour l'environnement de staging.
Ce script crée toutes les tables nécessaires directement à partir des modèles SQLAlchemy.
"""

import asyncio
import sys
import os
from pathlib import Path

# Ajouter le répertoire backend au chemin Python
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

# Vérifier que le chemin est correct
print(f"🔍 Recherche des modules dans: {backend_path}")

# Importer les modules nécessaires
try:
    from app.core.config import settings
    from app.db.base import Base
    from app.db.session import engine, get_db
    from sqlalchemy.ext.asyncio import create_async_engine
    print("✅ Modules importés avec succès")
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("Vérifiez que vous êtes dans le bon répertoire et que les dépendances sont installées.")
    sys.exit(1)

async def init_db():
    """Initialise la base de données en créant toutes les tables."""
    try:
        # Créer toutes les tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Base de données initialisée avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Démarrage de l'initialisation de la base de données...")
    print(f"📂 Base de données: {settings.DATABASE_URL}")
    
    # Créer le répertoire de la base de données si nécessaire
    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.split("///")[-1]
        db_dir = Path(db_path).parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Répertoire de la base de données créé: {db_dir}")
    
    # Exécuter l'initialisation
    success = asyncio.run(init_db())
    if not success:
        sys.exit(1)
