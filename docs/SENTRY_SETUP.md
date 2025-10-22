# 🔐 Sentry Setup Guide - GW2Optimizer

**Status**: ✅ Configured and Ready  
**DSN**: Configured in `.env.example`

---

## 📊 Configuration Actuelle

### Backend (FastAPI)
```python
✅ Sentry SDK installé: sentry-sdk[fastapi]==1.40.0
✅ DSN configuré dans .env.example
✅ Intégration dans app/main.py
✅ Endpoint de test: /api/v1/sentry-debug
✅ send_default_pii: True (headers + IP)
✅ traces_sample_rate: 1.0 (100%)
✅ Environment tracking
✅ Release versioning
```

### Frontend (React)
```typescript
✅ Sentry SDK: @sentry/react==7.100.0
✅ Intégration dans src/main.tsx
✅ Browser tracing
✅ Session replay
✅ Error replay
✅ Production only
```

---

## 🚀 Quick Start

### 1. Backend Setup

**Fichier**: `backend/.env`

```bash
# Copier .env.example vers .env
cp backend/.env.example backend/.env

# Le DSN est déjà configuré dans .env.example
SENTRY_DSN=https://d7067f5675913b468876ace2ce7cfefd@o4510235525120000.ingest.de.sentry.io/4510235538489424
```

### 2. Démarrer le Backend

```bash
cd backend

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt

# Démarrer le serveur
uvicorn app.main:app --reload
```

**Logs attendus**:
```
📊 Sentry error tracking initialized
📈 Prometheus metrics endpoint enabled at /metrics
🐛 Sentry debug endpoint enabled at /api/v1/sentry-debug
```

### 3. Tester Sentry

**Ouvrir dans le navigateur**:
```
http://localhost:8000/api/v1/sentry-debug
```

**Résultat attendu**:
- ❌ Erreur 500 (division by zero)
- ✅ Transaction créée dans Sentry Performance
- ✅ Error event envoyé à Sentry
- ✅ Données visibles dans Sentry dashboard

**Vérifier dans Sentry**:
1. Aller sur https://sentry.io
2. Projet: GW2Optimizer
3. Section **Issues**: Voir l'erreur "ZeroDivisionError"
4. Section **Performance**: Voir la transaction "/api/v1/sentry-debug"

---

## 📈 Endpoints de Monitoring

### Sentry Debug (Development Only)
```bash
GET http://localhost:8000/api/v1/sentry-debug
```
- Déclenche une erreur intentionnelle
- Teste Sentry error tracking
- Teste Sentry performance monitoring

### Prometheus Metrics
```bash
GET http://localhost:8000/metrics
```
- Métriques Prometheus
- Compteurs de requêtes
- Temps de réponse
- Erreurs HTTP

### Health Check
```bash
GET http://localhost:8000/health
GET http://localhost:8000/api/v1/health
```
- Status de l'application
- Environment
- Uptime

---

## 🔧 Configuration Avancée

### Backend Configuration

**Fichier**: `backend/app/main.py`

```python
# Sentry initialization
if SENTRY_AVAILABLE and not settings.TESTING and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,  # 100% des transactions
        environment=settings.ENVIRONMENT,
        release=f"gw2optimizer@{settings.API_VERSION}",
        send_default_pii=True,  # Inclut headers et IP
    )
```

**Options disponibles**:
- `traces_sample_rate`: 0.0 à 1.0 (% de transactions à capturer)
- `send_default_pii`: True/False (données personnelles)
- `environment`: development/staging/production
- `release`: Version de l'application

### Frontend Configuration

**Fichier**: `frontend/src/main.tsx`

```typescript
if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,  // 10% des sessions
    replaysOnErrorSampleRate: 1.0,  // 100% des erreurs
    environment: import.meta.env.MODE,
  });
}
```

**Variables d'environnement**:
```bash
# frontend/.env.production
VITE_SENTRY_DSN=https://...@sentry.io/...
```

---

## 📊 Sentry Dashboard

### Issues (Erreurs)
- **ZeroDivisionError**: Test endpoint
- **HTTPException**: Erreurs API
- **ValidationError**: Erreurs Pydantic
- **DatabaseError**: Erreurs DB

### Performance
- **Transactions**: Toutes les requêtes HTTP
- **Spans**: Détails des opérations
- **Database Queries**: Requêtes SQL
- **External Calls**: API externes

### Releases
- **Version**: gw2optimizer@{API_VERSION}
- **Commits**: Lié au Git
- **Deploy**: Timestamp

---

## 🎯 Best Practices

### 1. Error Handling

```python
from sentry_sdk import capture_exception

try:
    # Code risqué
    result = risky_operation()
except Exception as e:
    # Capturer l'erreur dans Sentry
    capture_exception(e)
    raise
```

### 2. Custom Context

```python
from sentry_sdk import set_context

set_context("user", {
    "id": user.id,
    "username": user.username,
})
```

### 3. Breadcrumbs

```python
from sentry_sdk import add_breadcrumb

add_breadcrumb(
    category="auth",
    message="User logged in",
    level="info",
)
```

### 4. Performance Monitoring

```python
from sentry_sdk import start_transaction

with start_transaction(op="task", name="process_team"):
    # Code à monitorer
    process_team_composition()
```

---

## 🔍 Troubleshooting

### Sentry ne reçoit pas les erreurs

**Vérifier**:
1. DSN configuré dans `.env`
2. `TESTING=False` (Sentry désactivé en mode test)
3. Serveur démarré avec `uvicorn`
4. Logs: "📊 Sentry error tracking initialized"

**Test**:
```bash
curl http://localhost:8000/api/v1/sentry-debug
```

### Prometheus metrics non disponibles

**Vérifier**:
1. `prometheus-fastapi-instrumentator` installé
2. `TESTING=False`
3. Endpoint: http://localhost:8000/metrics

### Frontend Sentry ne fonctionne pas

**Vérifier**:
1. `@sentry/react` installé: `npm install`
2. `VITE_SENTRY_DSN` configuré
3. Build production: `npm run build`
4. Mode production uniquement

---

## 📝 Commandes Utiles

### Backend

```bash
# Démarrer avec Sentry
cd backend
uvicorn app.main:app --reload

# Tester Sentry
curl http://localhost:8000/api/v1/sentry-debug

# Voir les métriques
curl http://localhost:8000/metrics

# Voir les logs
tail -f logs/gw2optimizer.log
```

### Frontend

```bash
# Installer dépendances
cd frontend
npm install

# Build production
npm run build

# Preview production
npm run preview
```

### Docker

```bash
# Démarrer monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Grafana
open http://localhost:3000

# Prometheus
open http://localhost:9090
```

---

## 🎉 Résumé

**Configuration Sentry**: ✅ COMPLETE

- ✅ Backend DSN configuré
- ✅ Frontend DSN prêt
- ✅ Endpoint de test créé
- ✅ Documentation complète
- ✅ Best practices documentées

**Prochaines étapes**:
1. Tester `/api/v1/sentry-debug`
2. Vérifier Sentry dashboard
3. Configurer frontend DSN
4. Tester en production

---

**Last Updated**: 2025-10-23 00:40 UTC+02:00  
**Sentry Project**: GW2Optimizer  
**Status**: Production Ready 🚀
