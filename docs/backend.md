# GW2Optimizer Backend Documentation

## Table des matières

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [API Endpoints](#api-endpoints)
5. [Base de données](#base-de-données)
6. [Authentification](#authentification)
7. [Cache](#cache)
8. [Apprentissage automatique](#apprentissage-automatique)
9. [Exemples d'utilisation](#exemples-dutilisation)

---

## Architecture

Le backend GW2Optimizer est construit avec :

- **FastAPI** : Framework web moderne et performant
- **SQLAlchemy** : ORM async pour PostgreSQL/SQLite
- **Alembic** : Gestion des migrations de base de données
- **Redis** : Cache distribué avec fallback disque
- **Ollama** : IA locale (Mistral 7B) pour génération de builds
- **Pydantic v2** : Validation de données et sérialisation

### Structure du projet

```
backend/
├── app/
│   ├── api/              # Endpoints REST
│   │   ├── auth.py       # Authentification JWT
│   │   ├── builds_db.py  # Gestion des builds (DB)
│   │   ├── teams_db.py   # Gestion des équipes (DB)
│   │   └── ...
│   ├── core/             # Configuration et utilitaires
│   │   ├── config.py     # Settings
│   │   ├── cache.py      # Gestion du cache
│   │   └── logging.py    # Logging
│   ├── db/               # Base de données
│   │   ├── base.py       # Configuration SQLAlchemy
│   │   └── init_db.py    # Initialisation
│   ├── models/           # Modèles de données
│   │   ├── user.py       # Modèle User
│   │   ├── build.py      # Modèle Build
│   │   └── team.py       # Modèle Team
│   ├── services/         # Logique métier
│   │   ├── auth_service.py
│   │   ├── build_service_db.py
│   │   └── team_service_db.py
│   └── learning/         # Apprentissage automatique
│       ├── data/         # Collecte de données
│       ├── models/       # Modèles ML (futur)
│       └── utils/        # Utilitaires
├── alembic/              # Migrations
├── tests/                # Tests unitaires
├── pyproject.toml        # Dépendances (Poetry)
└── poetry.lock           # Verrouillage des versions
```

---

## Installation

### Prérequis

- Python 3.11+
- PostgreSQL 14+ (ou SQLite pour dev)
- Redis 6+ (optionnel)
- Ollama avec Mistral 7B

### Installation des dépendances

```bash
cd backend
poetry install
```

### Configuration de la base de données

```bash
# Créer le fichier .env
cp ../.env.example .env

# Éditer .env avec vos paramètres
nano .env

# Appliquer les migrations
alembic upgrade head
```

### Lancement du serveur

```bash
# Mode développement
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Mode production (exemple)
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True

# Base de données
DATABASE_URL=sqlite+aiosqlite:///./gw2optimizer.db
# DATABASE_URL=postgresql://user:password@localhost:5432/gw2optimizer
DATABASE_ECHO=False

# Authentification
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cache
CACHE_TTL=3600
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# Learning
LEARNING_DATA_DIR=./data/learning
MAX_LEARNING_ITEMS=10000
LEARNING_ENABLED=true

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest
```

---

## API Endpoints

### Authentification

#### `POST /api/v1/auth/register`

Créer un nouveau compte utilisateur.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "player123",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "player123",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

#### `POST /api/v1/auth/login`

Se connecter et obtenir des tokens JWT.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### `GET /api/v1/auth/me`

Obtenir le profil de l'utilisateur connecté.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "player123",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

---

### Builds

#### `POST /api/v1/builds`

Créer un nouveau build.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "name": "Firebrand Support",
  "profession": "Guardian",
  "specialization": "Firebrand",
  "game_mode": "zerg",
  "role": "support",
  "description": "Boon support build for zergs",
  "is_public": true,
  "trait_lines": [
    {
      "id": 42,
      "name": "Firebrand",
      "traits": [2075, 2101, 2159]
    }
  ],
  "skills": [
    {
      "slot": "heal",
      "id": 9153,
      "name": "Mantra of Solace"
    }
  ],
  "equipment": [
    {
      "slot": "helm",
      "id": 48075,
      "name": "Harrier's Helm",
      "stats": "Harrier",
      "rune_or_sigil": 24842
    }
  ],
  "synergies": ["Might", "Quickness", "Stability"],
  "counters": ["Necromancer", "Scourge"]
}
```

**Response:**
```json
{
  "id": "build-uuid-here",
  "user_id": "user-uuid-here",
  "name": "Firebrand Support",
  "profession": "Guardian",
  "specialization": "Firebrand",
  "game_mode": "zerg",
  "role": "support",
  "description": "Boon support build for zergs",
  "is_public": true,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z",
  "trait_lines": [...],
  "skills": [...],
  "equipment": [...],
  "synergies": ["Might", "Quickness", "Stability"],
  "counters": ["Necromancer", "Scourge"]
}
```

#### `GET /api/v1/builds`

Lister les builds de l'utilisateur connecté.

**Query Parameters:**
- `skip` (int): Nombre d'éléments à sauter (pagination)
- `limit` (int): Nombre maximum d'éléments à retourner (max 100)
- `profession` (string): Filtrer par profession
- `game_mode` (string): Filtrer par mode de jeu
- `role` (string): Filtrer par rôle
- `is_public` (bool): Filtrer par statut public

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": "build-uuid-1",
    "name": "Firebrand Support",
    "profession": "Guardian",
    ...
  },
  {
    "id": "build-uuid-2",
    "name": "Scourge DPS",
    "profession": "Necromancer",
    ...
  }
]
```

#### `GET /api/v1/builds/public/all`

Lister les builds publics (pas d'authentification requise).

**Query Parameters:**
- `skip` (int): Nombre d'éléments à sauter
- `limit` (int): Nombre maximum d'éléments
- `profession` (string): Filtrer par profession
- `game_mode` (string): Filtrer par mode de jeu
- `role` (string): Filtrer par rôle

**Response:**
```json
[
  {
    "id": "build-uuid-1",
    "name": "Firebrand Support",
    "is_public": true,
    ...
  }
]
```

#### `GET /api/v1/builds/{build_id}`

Obtenir un build spécifique.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "build-uuid-here",
  "name": "Firebrand Support",
  ...
}
```

#### `PUT /api/v1/builds/{build_id}`

Mettre à jour un build.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "name": "Updated Build Name",
  "description": "Updated description",
  "is_public": false
}
```

#### `DELETE /api/v1/builds/{build_id}`

Supprimer un build.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

---

### Teams

#### `POST /api/v1/teams`

Créer une nouvelle composition d'équipe.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "name": "Zerg Composition",
  "game_mode": "zerg",
  "team_size": 15,
  "description": "Standard zerg composition",
  "is_public": true,
  "build_ids": [
    "build-uuid-1",
    "build-uuid-2",
    "build-uuid-3"
  ]
}
```

**Response:**
```json
{
  "id": "team-uuid-here",
  "user_id": "user-uuid-here",
  "name": "Zerg Composition",
  "game_mode": "zerg",
  "team_size": 15,
  "description": "Standard zerg composition",
  "is_public": true,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z",
  "slots": [...],
  "synergies": [],
  "weaknesses": [],
  "strengths": []
}
```

#### `GET /api/v1/teams`

Lister les équipes de l'utilisateur.

**Query Parameters:**
- `skip` (int): Pagination
- `limit` (int): Limite (max 100)
- `game_mode` (string): Filtrer par mode de jeu
- `is_public` (bool): Filtrer par statut public

**Headers:**
```
Authorization: Bearer <access_token>
```

#### `GET /api/v1/teams/public/all`

Lister les équipes publiques.

#### `POST /api/v1/teams/{team_id}/builds/{build_id}`

Ajouter un build à une équipe.

**Query Parameters:**
- `slot_number` (int): Numéro de slot (optionnel)
- `player_name` (string): Nom du joueur (optionnel)

**Headers:**
```
Authorization: Bearer <access_token>
```

#### `DELETE /api/v1/teams/{team_id}/slots/{slot_id}`

Retirer un build d'une équipe.

---

## Base de données

### Modèles

#### User
- `id` (UUID): Identifiant unique
- `email` (string): Email unique
- `username` (string): Nom d'utilisateur unique
- `hashed_password` (string): Mot de passe hashé
- `is_active` (bool): Compte actif
- `is_superuser` (bool): Super utilisateur
- `created_at` (datetime): Date de création
- `updated_at` (datetime): Date de mise à jour

**Relations:**
- `builds` (one-to-many): Builds créés par l'utilisateur
- `team_compositions` (one-to-many): Équipes créées par l'utilisateur

#### Build
- `id` (UUID): Identifiant unique
- `user_id` (UUID): Propriétaire du build
- `name` (string): Nom du build
- `profession` (string): Profession GW2
- `specialization` (string): Spécialisation
- `game_mode` (string): Mode de jeu (roaming, raid_guild, zerg)
- `role` (string): Rôle (tank, dps, support, healer, boonshare, utility)
- `trait_lines` (JSON): Lignes de traits
- `skills` (JSON): Compétences
- `equipment` (JSON): Équipement
- `synergies` (JSON): Synergies
- `counters` (JSON): Contres
- `description` (text): Description
- `playstyle` (text): Style de jeu
- `source_url` (string): URL source
- `source_type` (string): Type de source
- `effectiveness` (float): Efficacité (0-10)
- `difficulty` (int): Difficulté (1-5)
- `is_public` (bool): Public
- `created_at` (datetime): Date de création
- `updated_at` (datetime): Date de mise à jour

**Relations:**
- `user` (many-to-one): Propriétaire
- `team_slots` (one-to-many): Slots d'équipe

#### TeamComposition
- `id` (UUID): Identifiant unique
- `user_id` (UUID): Propriétaire
- `name` (string): Nom de l'équipe
- `game_mode` (string): Mode de jeu
- `team_size` (int): Taille de l'équipe
- `synergies` (JSON): Synergies
- `weaknesses` (JSON): Faiblesses
- `strengths` (JSON): Forces
- `description` (text): Description
- `overall_rating` (float): Note globale
- `is_public` (bool): Public
- `created_at` (datetime): Date de création
- `updated_at` (datetime): Date de mise à jour

**Relations:**
- `user` (many-to-one): Propriétaire
- `team_slots` (one-to-many): Slots avec builds

#### TeamSlot
- `id` (UUID): Identifiant unique
- `team_composition_id` (UUID): Équipe
- `build_id` (UUID): Build assigné
- `slot_number` (int): Numéro de slot
- `player_name` (string): Nom du joueur
- `priority` (int): Priorité (1-5)

### Migrations

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "Description"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

---

## Authentification

Le système utilise JWT (JSON Web Tokens) avec deux types de tokens :

- **Access Token** : Durée de vie courte (30 min par défaut)
- **Refresh Token** : Durée de vie longue (7 jours par défaut)

### Workflow

1. **Inscription** : `POST /api/v1/auth/register`
2. **Connexion** : `POST /api/v1/auth/login` → Obtenir access_token + refresh_token
3. **Utilisation** : Inclure `Authorization: Bearer <access_token>` dans les headers
4. **Rafraîchissement** : `POST /api/v1/auth/refresh` avec refresh_token

### Sécurité

- Mots de passe hashés avec bcrypt
- Tokens signés avec HS256
- Validation stricte des données (Pydantic)
- Protection CORS configurée

---

## Cache

Le système de cache utilise Redis avec fallback automatique sur disque.

### Utilisation

```python
from app.core.cache import cacheable, invalidate_cache

# Mettre en cache une fonction
@cacheable("build:{build_id}", ttl=3600)
async def get_build(build_id: str):
    # ... opération coûteuse ...
    return build

# Invalider le cache
@invalidate_cache("build:{build_id}")
async def update_build(build_id: str, data: dict):
    # ... mise à jour ...
    return updated_build
```

### Configuration

- **TTL par défaut** : 3600 secondes (1 heure)
- **Fallback disque** : `data/cache/`
- **Clés de cache** :
  - `build:{build_id}` : Build individuel
  - `builds:public:{filters}` : Liste de builds publics
  - `team:{team_id}` : Équipe individuelle
  - `teams:public:{filters}` : Liste d'équipes publiques

---

## Apprentissage automatique

Le module `learning/` collecte anonymement les interactions utilisateur pour améliorer les recommandations.

### Données collectées

- Création de builds (profession, mode de jeu, rôle)
- Création d'équipes (taille, composition)
- Évaluations de builds
- Utilisation de builds dans des équipes

### Conformité RGPD

- ✅ Données anonymisées
- ✅ Stockage local uniquement
- ✅ Purge automatique (90 jours par défaut)
- ✅ Limite de taille (10 000 interactions max)
- ✅ Désactivable via `LEARNING_ENABLED=false`

### Statistiques

```bash
GET /api/v1/learning/stats
```

---

## Exemples d'utilisation

### Workflow complet : Créer un build et une équipe

```python
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # 1. S'inscrire
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "player@example.com",
                "username": "player123",
                "password": "SecurePass123!"
            }
        )
        print("Registered:", register_response.json())
        
        # 2. Se connecter
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "player@example.com",
                "password": "SecurePass123!"
            }
        )
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Créer un build
        build_response = await client.post(
            f"{BASE_URL}/builds",
            headers=headers,
            json={
                "name": "Firebrand Support",
                "profession": "Guardian",
                "specialization": "Firebrand",
                "game_mode": "zerg",
                "role": "support",
                "is_public": True,
                "trait_lines": [],
                "skills": [],
                "equipment": []
            }
        )
        build = build_response.json()
        build_id = build["id"]
        print("Build created:", build_id)
        
        # 4. Créer une équipe avec ce build
        team_response = await client.post(
            f"{BASE_URL}/teams",
            headers=headers,
            json={
                "name": "My Zerg Team",
                "game_mode": "zerg",
                "team_size": 15,
                "is_public": False,
                "build_ids": [build_id]
            }
        )
        team = team_response.json()
        print("Team created:", team["id"])
        
        # 5. Lister mes builds
        builds_response = await client.get(
            f"{BASE_URL}/builds",
            headers=headers
        )
        print("My builds:", builds_response.json())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_builds.py
pytest tests/test_auth.py
```

---

## Déploiement

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copier la configuration Poetry
COPY pyproject.toml poetry.lock ./

# Installer les dépendances avec Poetry (sans virtualenv dédié)
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main

# Copier le code applicatif
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/gw2optimizer
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=gw2optimizer
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Support

Pour toute question ou problème :
- GitHub Issues : https://github.com/yourusername/GW2Optimizer/issues
- Documentation : https://gw2optimizer.readthedocs.io

---

**Version** : 1.2.0  
**Dernière mise à jour** : 2024-01-20
