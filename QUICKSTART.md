# GW2Optimizer - Quick Start Guide

## 🚀 Installation Rapide

### Prérequis
- Python 3.11+
- Node.js 18+
- Ollama ([Installation](https://ollama.ai))

### Installation Automatique

```bash
# Cloner le projet
git clone https://github.com/yourusername/GW2Optimizer.git
cd GW2Optimizer

# Exécuter le script de setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres
```

### Configuration Ollama

```bash
# Démarrer Ollama
ollama serve

# Dans un autre terminal, télécharger Mistral
ollama pull mistral
```

## 🎯 Lancement

### Option 1: Scripts automatiques

**Terminal 1 - Backend:**
```bash
./scripts/start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
./scripts/start-frontend.sh
```

### Option 2: Lancement manuel

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 📍 Accès

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

## 🧪 Tests

```bash
# Tous les tests
./scripts/run-tests.sh

# Backend uniquement
cd backend
pytest -v

# Avec couverture
pytest --cov=app --cov-report=html
```

## 📖 Utilisation

### 1. Chat avec l'IA

Accédez à l'onglet **Chat** et posez vos questions :
- "Crée une composition zerg pour 25 joueurs"
- "Quel est le meilleur build Guardian pour WvW ?"
- Collez un lien GW2Skill pour analyse

### 2. Créer un Build

Via l'API :
```bash
curl -X POST http://localhost:8000/api/v1/builds \
  -H "Content-Type: application/json" \
  -d '{
    "profession": "Guardian",
    "game_mode": "zerg",
    "role": "support"
  }'
```

### 3. Optimiser une Équipe

Via l'API :
```bash
curl -X POST http://localhost:8000/api/v1/teams/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "game_mode": "zerg",
    "team_size": 25,
    "required_roles": {"tank": 2, "support": 5, "dps": 18}
  }'
```

### 4. Statistiques d'Apprentissage

Accédez à l'onglet **Stats** pour voir :
- Nombre de builds collectés
- Score de qualité moyen
- Distribution des sources
- Progression de l'apprentissage

## 🔧 Configuration Avancée

### Learning Pipeline

Le pipeline d'apprentissage s'exécute automatiquement :
- **Quotidien**: À 3h00 (configurable dans `scheduler.py`)
- **Manuel**: Via `/api/v1/learning/pipeline/run`

### Personnalisation

Éditez les configurations dans `.env` :
```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# Learning
MIN_QUALITY_THRESHOLD=7.0
TRAINING_INTERVAL_DAYS=7

# Storage
MAX_STORAGE_GB=5.0
ARCHIVE_THRESHOLD_DAYS=30
```

## 🐛 Dépannage

### Ollama non connecté
```bash
# Vérifier si Ollama tourne
curl http://localhost:11434/api/tags

# Redémarrer Ollama
ollama serve
```

### Port déjà utilisé
```bash
# Changer le port backend dans .env
BACKEND_PORT=8001

# Changer le port frontend dans vite.config.ts
server: { port: 5174 }
```

### Erreur de dépendances
```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentation Complète

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [README](README.md)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📞 Support

- Issues: https://github.com/yourusername/GW2Optimizer/issues
- Discord: https://discord.gg/gw2optimizer
