# 📦 Guide d'Installation - GW2Optimizer

**Version**: v1.2.0  
**Date**: 20 Octobre 2025

---

## 🎯 Prérequis

### Système
- **OS**: Linux, macOS, ou Windows (WSL recommandé)
- **Python**: 3.10 ou supérieur
- **Node.js**: 18 ou supérieur
- **npm**: 9 ou supérieur

### Services
- **PostgreSQL**: 14+ (ou SQLite pour développement)
- **Redis**: 6+ (optionnel mais recommandé)
- **Ollama**: Dernière version avec Mistral 7B

---

## 🚀 Installation Backend

### 1. Cloner le Repository
```bash
git clone https://github.com/votre-repo/GW2Optimizer.git
cd GW2Optimizer
```

### 2. Créer l'Environnement Virtuel
```bash
cd backend
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Installer les Dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurer les Variables d'Environnement
```bash
cp .env.example .env
# Éditer .env avec vos valeurs
nano .env
```

**Variables critiques à configurer**:
```bash
SECRET_KEY=votre-cle-secrete-min-32-caracteres
DATABASE_URL=sqlite+aiosqlite:///./gw2optimizer.db
OLLAMA_HOST=http://localhost:11434
REDIS_URL=redis://localhost:6379/0
```

### 5. Initialiser la Base de Données
```bash
# Créer les tables
alembic upgrade head

# Vérifier
alembic current
```

### 6. Installer et Configurer Ollama
```bash
# Installer Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger Mistral 7B
ollama pull mistral

# Démarrer Ollama (dans un terminal séparé)
ollama serve
```

### 7. Démarrer Redis (Optionnel)
```bash
# Linux/macOS
redis-server

# Docker
docker run -d -p 6379:6379 redis:latest
```

### 8. Lancer le Serveur Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Vérification**:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

---

## 🎨 Installation Frontend

### 1. Naviguer vers le Dossier Frontend
```bash
cd ../frontend
```

### 2. Installer les Dépendances
```bash
npm install
```

### 3. Configurer les Variables d'Environnement
```bash
cp .env.example .env
# Éditer .env
nano .env
```

**Variables à configurer**:
```bash
VITE_API_URL=http://localhost:8000
VITE_API_BASE_PATH=/api/v1
```

### 4. Lancer le Serveur de Développement
```bash
npm run dev
```

**Vérification**:
- Application: http://localhost:5173

---

## 🧪 Exécuter les Tests

### Tests Backend
```bash
cd backend

# Tous les tests
pytest -v

# Tests spécifiques
pytest tests/test_auth.py -v
pytest tests/test_agents.py -v
pytest tests/test_workflows.py -v

# Avec coverage
pytest --cov=app --cov-report=html
# Ouvrir htmlcov/index.html
```

### Tests Frontend
```bash
cd frontend

# Tests unitaires
npm run test

# Tests E2E (si configurés)
npm run test:e2e
```

---

## 🔧 Configuration Avancée

### PostgreSQL (Production)

#### 1. Installer PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
```

#### 2. Créer la Base de Données
```bash
sudo -u postgres psql

CREATE DATABASE gw2optimizer;
CREATE USER gw2user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE gw2optimizer TO gw2user;
\q
```

#### 3. Mettre à Jour .env
```bash
DATABASE_URL=postgresql+asyncpg://gw2user:votre_mot_de_passe@localhost:5432/gw2optimizer
```

#### 4. Migrer
```bash
alembic upgrade head
```

### Redis (Production)

#### Configuration Redis
```bash
# Éditer redis.conf
sudo nano /etc/redis/redis.conf

# Activer la persistance
save 900 1
save 300 10
save 60 10000

# Redémarrer
sudo systemctl restart redis
```

### Ollama (Production)

#### Optimisation Mistral
```bash
# Utiliser GPU si disponible
OLLAMA_GPU=1 ollama serve

# Limiter la mémoire
OLLAMA_MAX_LOADED_MODELS=1 ollama serve
```

---

## 🐳 Installation avec Docker (Optionnel)

### 1. Créer docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://gw2user:password@db:5432/gw2optimizer
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - db
      - redis
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=gw2optimizer
      - POSTGRES_USER=gw2user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

### 2. Lancer avec Docker
```bash
docker-compose up -d
```

---

## 🔐 Configuration de Sécurité

### 1. Générer une Clé Secrète Sécurisée
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Configurer HTTPS (Production)
```bash
# Utiliser Nginx + Let's Encrypt
sudo apt install nginx certbot python3-certbot-nginx

# Obtenir certificat
sudo certbot --nginx -d votre-domaine.com
```

### 3. Configurer le Firewall
```bash
# UFW (Ubuntu)
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 📊 Vérification de l'Installation

### Checklist Backend
- [ ] Python 3.10+ installé
- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées
- [ ] .env configuré
- [ ] Base de données initialisée
- [ ] Ollama + Mistral installés
- [ ] Redis en cours d'exécution (optionnel)
- [ ] Serveur backend démarré
- [ ] http://localhost:8000/docs accessible

### Checklist Frontend
- [ ] Node.js 18+ installé
- [ ] Dépendances npm installées
- [ ] .env configuré
- [ ] Serveur frontend démarré
- [ ] http://localhost:5173 accessible

### Checklist Tests
- [ ] Tests backend passent (pytest)
- [ ] Coverage > 90%
- [ ] Tests frontend passent (npm test)

---

## 🐛 Dépannage

### Problème: Ollama ne démarre pas
```bash
# Vérifier le statut
systemctl status ollama

# Redémarrer
systemctl restart ollama

# Logs
journalctl -u ollama -f
```

### Problème: Redis connection refused
```bash
# Vérifier Redis
redis-cli ping

# Démarrer Redis
redis-server

# Ou désactiver Redis dans .env
REDIS_ENABLED=False
```

### Problème: Base de données locked
```bash
# SQLite
rm gw2optimizer.db
alembic upgrade head

# PostgreSQL
sudo systemctl restart postgresql
```

### Problème: Port déjà utilisé
```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 <PID>
```

---

## 📚 Ressources

### Documentation
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Ollama](https://ollama.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)

### Support
- **Issues**: GitHub Issues
- **Documentation**: `/docs` dans l'application
- **Logs**: `backend/logs/gw2optimizer.log`

---

## ✅ Installation Terminée

Votre installation de GW2Optimizer est maintenant complète !

**Prochaines étapes**:
1. Créer un compte utilisateur
2. Tester les recommandations de builds
3. Analyser des compositions d'équipe
4. Explorer la documentation API

**Bon jeu !** 🎮⚔️
