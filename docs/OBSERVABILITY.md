# Observability Guide

Guide complet pour monitorer GW2Optimizer en production.

## 📊 Stack d'Observabilité

### Composants
- **Prometheus** : Collecte de métriques
- **Grafana** : Visualisation et dashboards
- **Sentry** : Error tracking et performance monitoring
- **Structlog** : Structured logging (JSON)

### Architecture

```
┌─────────────┐
│   FastAPI   │
│  Backend    │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│ Prometheus  │  │   Sentry    │
│  /metrics   │  │   Errors    │
└──────┬──────┘  └─────────────┘
       │
       ▼
┌─────────────┐
│   Grafana   │
│  Dashboard  │
└─────────────┘
```

## 🚀 Quick Start

### 1. Démarrer Prometheus + Grafana

```bash
# Créer docker-compose.monitoring.yml
cd GW2Optimizer
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Configuration Prometheus

Créer `prometheus.yml` :

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'gw2optimizer'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
```

### 3. Accéder aux Dashboards

- **Prometheus** : http://localhost:9090
- **Grafana** : http://localhost:3000 (admin/admin)
- **Métriques Backend** : http://localhost:8000/metrics

## 📈 Métriques Disponibles

### HTTP Metrics (Auto)
Fournies par `prometheus-fastapi-instrumentator` :

- `http_requests_total` - Total des requêtes HTTP
- `http_request_duration_seconds` - Durée des requêtes (histogramme)
- `http_requests_in_progress` - Requêtes en cours
- `http_request_size_bytes` - Taille des requêtes
- `http_response_size_bytes` - Taille des réponses

### Custom AI Metrics

```python
# Utilisation dans le code
from app.core.metrics import track_ai_request

track_ai_request(
    model="mistral",
    operation="compose_team",
    duration=2.5,
    status="success",
    tokens_prompt=150,
    tokens_completion=300,
)
```

**Métriques** :
- `gw2_ai_requests_total{model, operation, status}` - Total requêtes IA
- `gw2_ai_request_duration_seconds{model, operation}` - Durée requêtes IA
- `gw2_ai_tokens_used_total{model, token_type}` - Tokens utilisés
- `gw2_ai_feedback_total{result}` - Feedbacks soumis
- `gw2_ai_training_triggers_total{result}` - Entraînements déclenchés

### Database Metrics

```python
from app.core.metrics import track_db_query

track_db_query(
    operation="select",
    table="builds",
    duration=0.05,
)
```

**Métriques** :
- `gw2_db_query_duration_seconds{operation, table}` - Durée queries
- `gw2_db_connections_active` - Connexions actives
- `gw2_db_errors_total{operation, error_type}` - Erreurs DB

### Cache Metrics

```python
from app.core.metrics import track_cache_operation

track_cache_operation(operation="get", result="hit")
```

**Métriques** :
- `gw2_cache_operations_total{operation, result}` - Opérations cache
- `gw2_cache_hit_rate` - Taux de hit cache (0-1)
- `gw2_cache_size_bytes` - Taille du cache

### External API Metrics

```python
from app.core.metrics import track_external_api

track_external_api(
    service="gw2api",
    endpoint="/v2/builds",
    duration=0.8,
    status="200",
)
```

**Métriques** :
- `gw2_external_api_requests_total{service, endpoint, status}` - Requêtes externes
- `gw2_external_api_duration_seconds{service, endpoint}` - Durée API externes

### Business Metrics

- `gw2_builds_created_total{profession, game_mode}` - Builds créés
- `gw2_teams_created_total{game_mode, size}` - Teams créées
- `gw2_users_active` - Utilisateurs actifs (24h)

### Application Info

- `gw2_app_info{version, environment}` - Info application

## 📊 Dashboards Grafana

### Dashboard 1 : System Overview

**Panels** :
1. **Request Rate** (Graph)
   ```promql
   rate(http_requests_total[5m])
   ```

2. **Error Rate** (Graph)
   ```promql
   rate(http_requests_total{status=~"5.."}[5m])
   ```

3. **Response Time P95** (Graph)
   ```promql
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```

4. **Active Users** (Stat)
   ```promql
   gw2_users_active
   ```

### Dashboard 2 : AI Performance

**Panels** :
1. **AI Requests by Model** (Graph)
   ```promql
   rate(gw2_ai_requests_total[5m])
   ```

2. **AI Request Duration P95** (Graph)
   ```promql
   histogram_quantile(0.95, rate(gw2_ai_request_duration_seconds_bucket[5m]))
   ```

3. **Tokens Used** (Graph)
   ```promql
   rate(gw2_ai_tokens_used_total[5m])
   ```

4. **AI Feedback Rate** (Graph)
   ```promql
   rate(gw2_ai_feedback_total[5m])
   ```

### Dashboard 3 : Database & Cache

**Panels** :
1. **DB Query Duration P95** (Graph)
   ```promql
   histogram_quantile(0.95, rate(gw2_db_query_duration_seconds_bucket[5m]))
   ```

2. **DB Connections** (Graph)
   ```promql
   gw2_db_connections_active
   ```

3. **Cache Hit Rate** (Gauge)
   ```promql
   gw2_cache_hit_rate
   ```

4. **Cache Operations** (Graph)
   ```promql
   rate(gw2_cache_operations_total[5m])
   ```

## 🔍 Structured Logging

### Configuration

Le backend utilise `structlog` pour des logs JSON structurés :

```python
from app.core.logging import logger

# Log simple
logger.info("User logged in", user_id=123, username="player1")

# Log avec contexte
logger.warning(
    "Slow AI request",
    model="mistral",
    duration=5.2,
    operation="compose_team",
)

# Log d'erreur
logger.error(
    "Database connection failed",
    error=str(e),
    retry_count=3,
)
```

### Format des Logs

**Development** (console colorée) :
```
2024-11-15T10:00:00.123Z [info     ] User logged in user_id=123 username=player1
```

**Production** (JSON) :
```json
{
  "event": "User logged in",
  "level": "info",
  "timestamp": "2024-11-15T10:00:00.123Z",
  "user_id": 123,
  "username": "player1"
}
```

### Agrégation des Logs

Pour agréger les logs en production, utilisez :
- **Loki** (recommandé, intégration Grafana native)
- **ELK Stack** (Elasticsearch + Logstash + Kibana)
- **CloudWatch Logs** (AWS)

## 🚨 Alerting

### Alertes Critiques (PagerDuty/Slack)

1. **Error Rate > 5%**
   ```yaml
   alert: HighErrorRate
   expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
   for: 5m
   annotations:
     summary: "High error rate detected"
   ```

2. **Response Time P95 > 2s**
   ```yaml
   alert: SlowResponses
   expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
   for: 5m
   ```

3. **Database Down**
   ```yaml
   alert: DatabaseDown
   expr: gw2_db_connections_active == 0
   for: 1m
   ```

### Alertes Warning (Email)

1. **Error Rate > 1%**
2. **Response Time P95 > 1s**
3. **Cache Hit Rate < 50%**
4. **Disk Usage > 80%**

## 🐛 Sentry Error Tracking

### Configuration

```bash
# Backend .env
SENTRY_DSN=https://xxx@sentry.io/xxx
ENVIRONMENT=production
```

### Utilisation

Sentry capture automatiquement :
- ✅ Exceptions non gérées
- ✅ Erreurs HTTP 5xx
- ✅ Performance traces (10% sample)

**Capture manuelle** :
```python
import sentry_sdk

try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

**Ajouter contexte** :
```python
with sentry_sdk.configure_scope() as scope:
    scope.set_user({"id": user_id, "username": username})
    scope.set_tag("game_mode", "WvW")
    scope.set_context("build", {"profession": "Guardian"})
```

## 📋 Checklist Production

Avant de déployer en production :

- [ ] Prometheus configuré et scraping `/metrics`
- [ ] Grafana dashboards créés et testés
- [ ] Sentry DSN configuré
- [ ] Alertes configurées (Slack/Email)
- [ ] Logs structurés activés (JSON)
- [ ] Log aggregation configurée (Loki/ELK)
- [ ] Runbook créé pour répondre aux alertes
- [ ] Équipe formée sur les outils

## 🔧 Troubleshooting

### Prometheus ne scrape pas les métriques

```bash
# Vérifier que /metrics est accessible
curl http://localhost:8000/metrics

# Vérifier la config Prometheus
docker-compose -f docker-compose.monitoring.yml logs prometheus
```

### Grafana ne se connecte pas à Prometheus

1. Aller dans Configuration > Data Sources
2. Ajouter Prometheus : `http://prometheus:9090`
3. Tester la connexion

### Logs non structurés

```bash
# Vérifier que structlog est installé
poetry show structlog

# Vérifier les logs
tail -f backend/logs/app.log
```

## 📚 Ressources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Structlog Docs](https://www.structlog.org/)

## 🎯 SLOs (Service Level Objectives)

### Targets

- **Availability** : 99.9% uptime
- **Latency P95** : < 200ms
- **Latency P99** : < 500ms
- **Error Rate** : < 1%
- **AI Request Success** : > 95%

### Monitoring

Suivre ces SLOs dans Grafana et configurer des alertes si les targets ne sont pas atteints.
