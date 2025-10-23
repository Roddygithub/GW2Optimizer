# 🏠 Déploiement Local - GW2Optimizer v3.0.0

Guide complet pour déployer GW2Optimizer localement sur votre PC.

---

## 📋 Prérequis

### Logiciels Requis
- **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Git**

### Vérification
```bash
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
git --version            # Git 2.0+
```

---

## 🚀 Installation Rapide (5 minutes)

### 1. Cloner le Repository
```bash
git clone https://github.com/Roddygithub/GW2Optimizer.git
cd GW2Optimizer
```

### 2. Configuration
```bash
# Copier le fichier de configuration local
cp .env.local .env

# Éditer si nécessaire (optionnel)
nano .env
```

**Variables à configurer (optionnel)**:
- `GW2_API_KEY` - Clé API Guild Wars 2 (optionnel pour tests)
- `MISTRAL_API_KEY` - Clé API Mistral AI (optionnel pour tests)
- `SECRET_KEY` - Changer en production

### 3. Lancer les Services
```bash
# Démarrer tous les services
docker-compose -f docker-compose.prod.yml up -d

# Vérifier que tout fonctionne
docker-compose -f docker-compose.prod.yml ps
```

### 4. Accéder à l'Application
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## 📊 Services Disponibles

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost | Interface utilisateur React |
| Backend | http://localhost:8000 | API FastAPI |
| API Docs | http://localhost:8000/docs | Documentation Swagger |
| Grafana | http://localhost:3000 | Dashboards monitoring |
| Prometheus | http://localhost:9090 | Métriques |
| PostgreSQL | localhost:5432 | Base de données |
| Redis | localhost:6379 | Cache |

---

## 🔧 Configuration Détaillée

### Variables d'Environnement

Le fichier `.env.local` contient déjà les bonnes valeurs:

```bash
# Sentry (Error Tracking) - Déjà configuré ✅
SENTRY_DSN=https://d7067f5675913b468876ace2ce7cfefd@...
VITE_SENTRY_DSN=https://bdd0ff8259b4cbc7214e79260ad04614@...

# API URL - Local ✅
VITE_API_URL=http://localhost:8000

# Database - Local ✅
DATABASE_URL=postgresql+asyncpg://gw2user:gw2password@postgres:5432/gw2optimizer

# Redis - Local ✅
REDIS_URL=redis://redis:6379/0
```

### APIs Externes (Optionnel)

#### GW2 API Key
1. Aller sur https://account.arena.net/applications
2. Créer une nouvelle clé API
3. Permissions recommandées: `account`, `characters`, `progression`
4. Copier la clé dans `.env`:
   ```bash
   GW2_API_KEY=VOTRE_CLE_ICI
   ```

#### Mistral AI Key
1. Aller sur https://console.mistral.ai/
2. Créer un compte (gratuit)
3. Générer une clé API
4. Copier la clé dans `.env`:
   ```bash
   MISTRAL_API_KEY=VOTRE_CLE_ICI
   ```

---

## 🎮 Utilisation

### Démarrer les Services
```bash
# Démarrer
docker-compose -f docker-compose.prod.yml up -d

# Voir les logs
docker-compose -f docker-compose.prod.yml logs -f

# Logs d'un service spécifique
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Arrêter les Services
```bash
# Arrêter (garde les données)
docker-compose -f docker-compose.prod.yml stop

# Arrêter et supprimer les conteneurs
docker-compose -f docker-compose.prod.yml down

# Arrêter et supprimer TOUT (données incluses)
docker-compose -f docker-compose.prod.yml down -v
```

### Redémarrer un Service
```bash
# Redémarrer le backend
docker-compose -f docker-compose.prod.yml restart backend

# Redémarrer tous les services
docker-compose -f docker-compose.prod.yml restart
```

### Mettre à Jour
```bash
# Récupérer les dernières modifications
git pull origin main

# Reconstruire les images
docker-compose -f docker-compose.prod.yml build

# Redémarrer
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🧪 Tests

### Health Check
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost

# Prometheus
curl http://localhost:9090/-/healthy
```

### Tester l'API
```bash
# Voir la documentation interactive
open http://localhost:8000/docs

# Test endpoint
curl http://localhost:8000/api/v1/health
```

---

## 📈 Monitoring

### Grafana Dashboards

1. **Accéder à Grafana**: http://localhost:3000
2. **Login**: admin / admin
3. **Dashboard**: "GW2Optimizer Main Dashboard"

**Métriques disponibles**:
- Taux de requêtes API
- Temps de réponse (p50, p95, p99)
- Taux d'erreurs
- Requêtes externes (GW2 API, Mistral AI)
- Cache hit rate
- Requêtes base de données

### Prometheus

1. **Accéder à Prometheus**: http://localhost:9090
2. **Explorer les métriques**: Onglet "Graph"
3. **Exemples de requêtes**:
   ```promql
   # Taux de requêtes
   rate(http_requests_total[5m])
   
   # Temps de réponse moyen
   rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
   
   # Taux d'erreurs
   rate(http_requests_total{status=~"5.."}[5m])
   ```

### Sentry (Error Tracking)

Les erreurs sont automatiquement envoyées à Sentry:
- **Backend**: https://sentry.io (projet GW2Optimizer Backend)
- **Frontend**: https://sentry.io (projet GW2Optimizer Frontend)

---

## 🔍 Dépannage

### Les services ne démarrent pas

**Vérifier Docker**:
```bash
docker ps
docker-compose -f docker-compose.prod.yml ps
```

**Voir les logs**:
```bash
docker-compose -f docker-compose.prod.yml logs
```

### Port déjà utilisé

Si un port est déjà utilisé (80, 8000, 3000, etc.):

**Option 1**: Arrêter le service qui utilise le port
```bash
# Linux/Mac
sudo lsof -i :80
sudo kill -9 <PID>

# Windows
netstat -ano | findstr :80
taskkill /PID <PID> /F
```

**Option 2**: Modifier les ports dans `docker-compose.prod.yml`
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Utiliser 8080 au lieu de 80
```

### Base de données ne se connecte pas

**Vérifier PostgreSQL**:
```bash
docker-compose -f docker-compose.prod.yml logs postgres
```

**Réinitialiser la base**:
```bash
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

### Problème de cache

**Vider le cache Redis**:
```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL
```

### Reconstruire les images

```bash
# Reconstruire tout
docker-compose -f docker-compose.prod.yml build --no-cache

# Reconstruire un service
docker-compose -f docker-compose.prod.yml build --no-cache backend
```

---

## 🛠️ Commandes Utiles

### Docker Compose
```bash
# Voir les services en cours
docker-compose -f docker-compose.prod.yml ps

# Voir les logs en temps réel
docker-compose -f docker-compose.prod.yml logs -f

# Exécuter une commande dans un conteneur
docker-compose -f docker-compose.prod.yml exec backend bash

# Voir l'utilisation des ressources
docker stats
```

### Base de Données
```bash
# Se connecter à PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U gw2user -d gw2optimizer

# Backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U gw2user gw2optimizer > backup.sql

# Restore
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T postgres psql -U gw2user -d gw2optimizer
```

### Redis
```bash
# Se connecter à Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Voir les clés
docker-compose -f docker-compose.prod.yml exec redis redis-cli KEYS '*'

# Vider le cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL
```

---

## 📊 Performance

### Ressources Recommandées

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB

**Recommandé**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB

### Optimisation

**Limiter les ressources Docker**:
```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 🔒 Sécurité

### Pour Utilisation Locale

La configuration par défaut est **sécurisée pour usage local**:
- ✅ Services accessibles uniquement en localhost
- ✅ Pas d'exposition internet
- ✅ Mots de passe par défaut OK pour local

### Pour Exposition Internet

Si vous voulez exposer l'application sur internet:

1. **Changer les mots de passe**:
   ```bash
   # .env
   POSTGRES_PASSWORD=mot_de_passe_fort
   SECRET_KEY=cle_secrete_32_caracteres_minimum
   GRAFANA_ADMIN_PASSWORD=mot_de_passe_fort
   ```

2. **Configurer HTTPS** (Nginx + Let's Encrypt)

3. **Configurer un firewall**

4. **Activer les limites de rate**

---

## 📚 Documentation Complète

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Guide de déploiement complet
- **[QUICK_TEST_GUIDE.md](./QUICK_TEST_GUIDE.md)** - Tests rapides (15 min)
- **[SENTRY_SETUP.md](./SENTRY_SETUP.md)** - Configuration Sentry
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture système
- **[API.md](./API.md)** - Documentation API

---

## 🎯 Résumé

### Démarrage Rapide
```bash
# 1. Clone
git clone https://github.com/Roddygithub/GW2Optimizer.git
cd GW2Optimizer

# 2. Configure
cp .env.local .env

# 3. Lance
docker-compose -f docker-compose.prod.yml up -d

# 4. Accède
open http://localhost
```

### URLs Importantes
- **App**: http://localhost
- **API**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3000

### Support
- **Issues**: https://github.com/Roddygithub/GW2Optimizer/issues
- **Docs**: https://github.com/Roddygithub/GW2Optimizer/tree/main/docs

---

**Version**: v3.0.0  
**Status**: Production Ready  
**Dernière mise à jour**: 2025-10-23
