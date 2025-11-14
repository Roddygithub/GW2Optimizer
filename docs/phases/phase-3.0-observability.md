# Phase 3.0 : Observabilité & Performance Monitoring

**Status**: Planned  
**Durée estimée**: 3-4 jours  
**Priorité**: Medium  
**Dépendances**: Phase 2.x completed ✅

---

## 🎯 Objectifs

Implémenter une observabilité complète pour monitorer la santé, les performances et les erreurs du système en production.

### Métriques de Succès
- ✅ Temps de réponse moyen < 200ms
- ✅ Error rate < 1%
- ✅ 99% uptime
- ✅ Alertes automatiques sur incidents
- ✅ Dashboard temps réel

---

## 📋 Prérequis

### Infrastructure
- [x] Backend stable (FastAPI)
- [x] CI/CD verte
- [x] Branch protection active
- [x] Tests automatisés

### Décisions Requises
- [ ] Choix stack monitoring (Prometheus vs Datadog vs New Relic)
- [ ] Budget Sentry (Free tier vs Team plan)
- [ ] Hébergement Grafana (self-hosted vs cloud)

---

## 🔧 Tâches Techniques

### 1. Prometheus Metrics (2-3h)
**Objectif**: Exposer métriques applicatives

```python
# backend/requirements.txt
prometheus-client==0.20.0
prometheus-fastapi-instrumentator==7.0.0

# backend/app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

**Métriques à tracker**:
- Request rate (req/s)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database query time
- Cache hit rate
- AI API latency

**Endpoints**:
- `/metrics` - Prometheus scraping endpoint
- `/health` - Health check (déjà existant)
- `/ready` - Readiness probe

### 2. Sentry Error Tracking (1-2h)
**Objectif**: Capturer et analyser les erreurs

```python
# backend/requirements.txt
sentry-sdk[fastapi]==2.0.0

# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=0.1,  # 10% des transactions
    profiles_sample_rate=0.1,
)
```

**Configuration**:
- [ ] Créer projet Sentry
- [ ] Ajouter SENTRY_DSN aux secrets GitHub
- [ ] Configurer alertes (Slack/Email)
- [ ] Définir error budgets

**Frontend**:
```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 0.1,
});
```

### 3. Structured Logging (2-3h)
**Objectif**: Logs JSON structurés pour analyse

```python
# backend/requirements.txt
structlog==24.1.0
python-json-logger==2.0.7

# backend/app/core/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()
```

**Logs à structurer**:
- API requests (method, path, status, duration)
- Database queries (query, duration, rows)
- AI API calls (model, tokens, cost, latency)
- Cache operations (hit/miss, key, ttl)
- Errors (exception, stack trace, context)

### 4. Performance Monitoring (1-2h)
**Objectif**: Tracker performance applicative

```python
# backend/app/middleware/performance.py
from fastapi import Request
import time

@app.middleware("http")
async def add_performance_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    # Log slow requests
    if duration > 1.0:
        logger.warning("slow_request", path=request.url.path, duration=duration)
    
    return response
```

**Métriques**:
- Database query time
- Redis latency
- AI API latency
- External API calls (GW2 API)

### 5. Dashboard Grafana (2-3h)
**Objectif**: Visualisation temps réel

**Option A: Self-hosted** (recommandé pour démarrer)
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Option B: Grafana Cloud** (payant mais géré)

**Dashboards à créer**:
1. **System Overview**
   - Request rate
   - Error rate
   - Response time (p50, p95, p99)
   - Active users

2. **API Performance**
   - Endpoint latency
   - Database queries
   - Cache hit rate
   - AI API usage

3. **Errors & Alerts**
   - Error rate by endpoint
   - 5xx errors
   - Failed AI calls
   - Database errors

### 6. Alerting (1h)
**Objectif**: Notifications automatiques

**Alertes critiques** (PagerDuty/Slack):
- Error rate > 5%
- Response time p95 > 2s
- Database down
- AI API quota exceeded

**Alertes warning** (Email):
- Error rate > 1%
- Response time p95 > 1s
- Cache miss rate > 50%
- Disk usage > 80%

---

## 📊 Livrables

### Code
- [ ] Prometheus metrics endpoint
- [ ] Sentry integration (backend + frontend)
- [ ] Structured logging
- [ ] Performance middleware
- [ ] Health checks avancés

### Infrastructure
- [ ] Prometheus server (Docker)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (optionnel: Loki)

### Documentation
- [ ] Runbook: Comment répondre aux alertes
- [ ] Dashboard guide
- [ ] Metrics catalog
- [ ] Troubleshooting guide

---

## 🚀 Plan d'Exécution

### Jour 1: Metrics & Logging
1. Installer Prometheus + instrumentator (1h)
2. Configurer structured logging (2h)
3. Ajouter custom metrics (1h)
4. Tests & validation (1h)

### Jour 2: Error Tracking
1. Setup Sentry backend (1h)
2. Setup Sentry frontend (1h)
3. Configurer alertes (1h)
4. Tester error capture (1h)

### Jour 3: Dashboards & Alerting
1. Installer Grafana (1h)
2. Créer dashboards (3h)
3. Configurer alerting (1h)
4. Documentation (1h)

### Jour 4: Testing & Refinement
1. Load testing (2h)
2. Alert testing (1h)
3. Documentation finale (2h)
4. Review & merge (1h)

---

## 💰 Coûts Estimés

### Free Tier (Recommandé pour démarrer)
- **Sentry**: 5K errors/month gratuit
- **Prometheus**: Self-hosted (gratuit)
- **Grafana**: Self-hosted (gratuit)
- **Total**: 0€/mois

### Paid Tier (Si besoin scale)
- **Sentry Team**: $26/mois (50K errors)
- **Grafana Cloud**: $49/mois (10K metrics)
- **Datadog**: $15/host/mois
- **Total**: ~$90/mois

**Recommandation**: Commencer avec free tier, upgrader si nécessaire.

---

## 🎯 Métriques de Succès

### Performance
- [ ] P50 response time < 100ms
- [ ] P95 response time < 200ms
- [ ] P99 response time < 500ms

### Reliability
- [ ] Uptime > 99%
- [ ] Error rate < 1%
- [ ] MTTR (Mean Time To Recovery) < 15min

### Observability
- [ ] 100% des endpoints instrumentés
- [ ] Alertes configurées pour tous les SLOs
- [ ] Dashboards accessibles à l'équipe

---

## 📚 Ressources

### Documentation
- [Prometheus FastAPI](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [Sentry FastAPI](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Structlog](https://www.structlog.org/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

### Exemples
- [FastAPI Observability Template](https://github.com/tiangolo/full-stack-fastapi-template)
- [Production-Ready FastAPI](https://github.com/zhanymkanov/fastapi-best-practices)

---

## 🔄 Dépendances

### Bloque
- Phase 4.0: Production Deployment (besoin monitoring avant prod)

### Bloqué par
- ✅ Phase 2.x: Cleanup & Optimization (TERMINÉ)

---

## 📝 Notes

### Décisions à prendre
1. **Monitoring Stack**: Prometheus/Grafana vs Datadog vs New Relic
   - **Recommandation**: Prometheus/Grafana (open-source, gratuit)
   
2. **Log Aggregation**: Loki vs ELK vs CloudWatch
   - **Recommandation**: Loki (intégration Grafana native)
   
3. **Alerting**: PagerDuty vs Opsgenie vs Slack
   - **Recommandation**: Slack pour démarrer (gratuit)

### Risques
- **Overhead performance**: Metrics collection peut ralentir l'app
  - **Mitigation**: Sampling (10% des traces)
  
- **Coûts Sentry**: Peut exploser avec beaucoup d'erreurs
  - **Mitigation**: Rate limiting + error grouping
  
- **Complexité**: Trop de dashboards = confusion
  - **Mitigation**: Commencer simple, itérer

---

## ✅ Checklist de Démarrage

Avant de commencer Phase 3.0:

- [x] Phase 2.x terminée
- [x] CI/CD verte
- [x] Tests passent
- [ ] Décision monitoring stack
- [ ] Budget approuvé (si paid tier)
- [ ] Accès Sentry/Grafana configurés
- [ ] Équipe formée sur les outils

**Status**: READY TO START 🚀
