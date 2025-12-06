# Service DataCollector

Le service `DataCollector` est responsable de la collecte, du stockage et de la récupération des données d'entraînement pour le système d'IA.

## Fonctionnalités

- Collecte des builds, des équipes et des métas-builds
- Compression des données pour un stockage efficace
- Persistance des données entre les redémarrages
- Gestion des erreurs et des données corrompues
- Support pour l'accès concurrentiel

## Utilisation

### Initialisation

```python
from app.services.learning.data_collector import DataCollector

# Créer une instance du collecteur de données
data_collector = DataCollector()
```

### Collecte d'un build

```python
from app.models.build import Build, GameMode, Profession, Role
from datetime import datetime
import uuid

# Créer un build de test
build = Build(
    id=str(uuid.uuid4()),
    user_id=str(uuid.uuid4()),
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    name="Firebrand Healer",
    profession=Profession.GUARDIAN,
    game_mode=GameMode.ZERG,
    role=Role.HEALER,
    specialization="Firebrand",
    trait_lines=[],
    skills=[],
    equipment=[],
    synergies=[],
    counters=[]
)

# Collecter le build
datapoint = await data_collector.collect_build(build)
```

### Récupération des données

```python
# Charger un point de données par son ID
datapoint = await data_collector.load_datapoint(datapoint_id)

# Récupérer tous les points de données
datapoints = await data_collector.get_all_datapoints()
```

## Structure des données

### TrainingDatapoint

- `id`: Identifiant unique du point de données
- `build_id`: ID du build associé (optionnel)
- `team_id`: ID de l'équipe associée (optionnel)
- `data`: Données brutes du build ou de l'équipe
- `game_mode`: Mode de jeu (roaming, raid_guild, zerg)
- `profession`: Profession du personnage (optionnel)
- `role`: Rôle du personnage (optionnel)
- `source`: Source des données (AI_GENERATED, PARSED_GW2SKILL, COMMUNITY_SCRAPE, USER_IMPORT)
- `compressed_size_bytes`: Taille des données compressées en octets
- `created_at`: Date de création

## Gestion des erreurs

Le service gère les erreurs suivantes :

- Données corrompues
- Fichiers manquants
- Accès concurrentiel
- Données invalides

## Tests

### Exécution des tests

```bash
# Exécuter tous les tests
poetry run pytest tests/test_services/test_data_collector.py -v

# Exécuter les tests d'intégration
poetry run pytest tests/test_services/test_data_collector_integration.py -v

# Exécuter les tests de cas limites
poetry run pytest tests/test_services/test_data_collector_edge_cases.py -v
```

### Ajout de nouveaux tests

Pour ajouter un nouveau test, créez une fonction dans le fichier de test approprié avec le décorateur `@pytest.mark.asyncio`.

```python
import pytest

@pytest.mark.asyncio
async def test_nouveau_cas():
    # Configuration du test
    # Exécution
    # Vérification
    pass
```

## Performance

Le service utilise la compression zlib pour réduire l'espace de stockage. Les performances typiques sont :

- Taux de compression : ~80% de réduction
- Temps de compression/décompression : < 1ms par point de données

## Sécurité

- Toutes les entrées sont validées avec Pydantic
- Les fichiers sont stockés avec des permissions restreintes
- Les erreurs sont enregistrées mais ne fuient pas d'informations sensibles
