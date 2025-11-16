# 🚀 RUNBOOK PRODUCTION - GW2Optimizer

**Version**: v0.5.0  
**Date**: 2025-11-16  
**Équipe**: DevOps / SRE

---

## 📋 GO-LIVE CHECKLIST (30-60 minutes)

### **Phase 1: Secrets & Configuration** (10 min)

#### **1.1 Backend Environment**
```bash
cd backend
cp .env.production.example .env

# Générer SECRET_KEY
openssl rand -hex 32

# Éditer .env avec:
# - SECRET_KEY (généré ci-dessus)
# - DATABASE_URL (PostgreSQL managé)
# - REDIS_URL
# - MISTRAL_API_KEY
# - SENTRY_DSN
# - ENVIRONMENT=production
```

#### **1.2 Rotation des Secrets**
```
Date de génération: 2025-11-16
Prochaine rotation: 2026-02-16 (trimestrielle)

Secrets à noter:
- SECRET_KEY: [date]
- DATABASE_PASSWORD: [date]
- MISTRAL_API_KEY: [date]
```

---

### **Phase 2: Déploiement** (15 min)

#### **2.1 Build & Deploy**
```bash
# 1. Build images
docker-compose -f docker-compose.prod.yml build

# 2. Migrations DB
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### **2.2 Vérification Containers**
```bash
# Status
docker-compose -f docker-compose.prod.yml ps

# Expected:
# backend    Up    0.0.0.0:8000->8000/tcp
# frontend   Up    0.0.0.0:5173->5173/tcp
# postgres   Up    5432/tcp
# redis      Up    6379/tcp
```

---

### **Phase 3: Sanity Checks** (10 min)

#### **3.1 API Health**
```bash
# Health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}

# API docs
curl http://localhost:8000/docs
# Expected: 200 OK

# Metrics
curl http://localhost:8000/metrics
# Expected: Prometheus metrics exposition
```

#### **3.2 Frontend**
```bash
# Homepage
curl -I http://localhost:5173
# Expected: HTTP/1.1 200 OK

# Assets loading
curl http://localhost:5173/assets/index.js
# Expected: 200 OK
```

#### **3.3 Database**
```bash
# Test connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.db.session import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('DB OK:', result.scalar())
"
```

#### **3.4 Redis**
```bash
# Test connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.redis import redis_client
import asyncio
async def test():
    await redis_client.ping()
    print('Redis OK')
asyncio.run(test())
"
```

#### **3.5 Sentry**
```bash
# Trigger test error
curl -X POST http://localhost:8000/api/v1/sentry-debug

# Check Sentry dashboard
# Expected: Event appears in https://sentry.io/organizations/.../issues/
```

---

### **Phase 4: Monitoring Setup** (15 min)

#### **4.1 Prometheus**
```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Prometheus
open http://localhost:9090

# Verify targets
# Status → Targets → All UP
```

#### **4.2 Grafana**
```bash
# Access Grafana
open http://localhost:3000
# Login: admin / admin (change on first login)

# Import dashboard
# + → Import → Upload JSON
# File: monitoring/dashboards/gw2optimizer-main.json
```

#### **4.3 Alert Rules**
```yaml
# monitoring/prometheus-alerts.yml
groups:
  - name: gw2optimizer
    interval: 30s
    rules:
      # 1. 5xx rate > 1% (5m)
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        
      # 2. p95 latency > 1s (5m)
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        
      # 3. Instance down (1m)
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        
      # 4. Scheduled pipeline failure
      - alert: PipelineFailure
        expr: learning_pipeline_failures_total > 0
        for: 5m
```

---

## 🧪 SMOKE TESTS (Jour J)

### **Auth Flow**
```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","username":"testuser"}'
# Expected: 201 Created

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test123!" \
  | jq -r '.access_token')

# 3. Get current user
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: User details
```

### **Builds CRUD**
```bash
# 1. Create build
BUILD_ID=$(curl -X POST http://localhost:8000/api/v1/builds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Build","profession":"Guardian","specialization":"Firebrand"}' \
  | jq -r '.id')

# 2. List builds
curl http://localhost:8000/api/v1/builds \
  -H "Authorization: Bearer $TOKEN"

# 3. Get build
curl http://localhost:8000/api/v1/builds/$BUILD_ID \
  -H "Authorization: Bearer $TOKEN"

# 4. Update build
curl -X PUT http://localhost:8000/api/v1/builds/$BUILD_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Build"}'

# 5. Delete build
curl -X DELETE http://localhost:8000/api/v1/builds/$BUILD_ID \
  -H "Authorization: Bearer $TOKEN"
```

### **Teams**
```bash
# 1. Create team
TEAM_ID=$(curl -X POST http://localhost:8000/api/v1/teams \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Team","game_mode":"zerg","size":50}' \
  | jq -r '.id')

# 2. Add member
curl -X POST http://localhost:8000/api/v1/teams/$TEAM_ID/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"build_id":"'$BUILD_ID'","role":"support"}'

# 3. List teams
curl http://localhost:8000/api/v1/teams \
  -H "Authorization: Bearer $TOKEN"

# 4. Get team
curl http://localhost:8000/api/v1/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN"
```

### **AI Services**
```bash
# 1. Compose team
curl -X POST http://localhost:8000/api/v1/ai/compose-team \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"game_mode":"zerg","team_size":50}'
# Expected: 200 OK or 503 (if Mistral unavailable)

# 2. Optimize build
curl -X POST http://localhost:8000/api/v1/ai/optimize-build \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"build_id":"'$BUILD_ID'","game_mode":"zerg"}'

# 3. Analyze synergy
curl -X POST http://localhost:8000/api/v1/ai/analyze-synergy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profession1":"Guardian","profession2":"Warrior"}'
```

---

## 📊 OBSERVABILITÉ LIVE

### **Grafana Dashboards**
```
1. Overview Dashboard
   - Request rate (req/s)
   - Error rate (%)
   - Latency (p50, p95, p99)
   - Active connections

2. Application Metrics
   - CPU usage (%)
   - Memory usage (MB)
   - DB connections
   - Redis hits/misses

3. Business Metrics
   - Active users
   - Builds created
   - Teams created
   - AI requests

4. Alerts
   - Active alerts
   - Alert history
   - Incident timeline
```

### **Sentry Monitoring**
```
Acceptable thresholds:
- Error rate: < 1 error/min
- 5xx rate: < 0.1%
- Timeout rate: < 0.5%

Alert on:
- Spike: > 10 errors/min
- New error type
- Critical error (DB down, Redis down)
```

### **Log Correlation**
```bash
# Find request by req_id
docker-compose logs backend | grep "req_id=abc123"

# Trace end-to-end flow
# 1. Request arrives (req_id generated)
# 2. Auth check (req_id logged)
# 3. DB query (req_id logged)
# 4. Response sent (req_id logged)
```

---

## 🔒 PRODUCTION HARDENING

### **HTTPS & Security Headers**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name gw2optimizer.com;

    ssl_certificate /etc/ssl/certs/gw2optimizer.crt;
    ssl_certificate_key /etc/ssl/private/gw2optimizer.key;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://localhost:5173;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### **Cookie Security**
```python
# backend/app/core/security.py
# Already configured in production:
SECURE_COOKIES = True
SAMESITE_COOKIES = "strict"
HTTPONLY_COOKIES = True
```

### **Rate Limiting**
```python
# backend/app/core/config.py
# Production values:
RATE_LIMIT_PER_MINUTE = 100
RATE_LIMIT_PER_HOUR = 2000

# Auth endpoints (stricter):
AUTH_RATE_LIMIT_PER_MINUTE = 10
AUTH_RATE_LIMIT_PER_HOUR = 50

# AI endpoints:
AI_RATE_LIMIT_PER_MINUTE = 30
AI_RATE_LIMIT_PER_HOUR = 500
```

---

## 💰 COÛTS & USAGE IA

### **Métriques Tokens**
```python
# Already instrumented in app/services/mistral_ai.py
mistral_tokens_used_total
mistral_requests_total
mistral_errors_total
```

### **Alerte Budget Journalier**
```yaml
# prometheus-alerts.yml
- alert: HighAICost
  expr: sum(increase(mistral_tokens_used_total[24h])) > 1000000
  annotations:
    summary: "Daily AI token usage exceeded 1M"
```

### **Fallback Heures Creuses**
```python
# backend/app/services/mistral_ai.py
# Configure off-peak hours (already implemented):
if is_off_peak_hours():
    return self._generate_fallback_composition()
```

---

## 💾 SAUVEGARDES

### **Database Backups**
```bash
# Daily backup script
#!/bin/bash
# /opt/scripts/backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="gw2optimizer_prod"

# Backup
pg_dump -h localhost -U gw2optimizer $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Retention (30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://gw2optimizer-backups/
```

### **Cron Schedule**
```cron
# Daily at 2 AM
0 2 * * * /opt/scripts/backup-db.sh

# Weekly restore test (Sunday 3 AM)
0 3 * * 0 /opt/scripts/test-restore.sh
```

### **Restore Test**
```bash
# /opt/scripts/test-restore.sh
#!/bin/bash

LATEST_BACKUP=$(ls -t /backups/postgres/backup_*.sql.gz | head -1)
TEST_DB="gw2optimizer_test_restore"

# Create test DB
createdb -h localhost -U gw2optimizer $TEST_DB

# Restore
gunzip -c $LATEST_BACKUP | psql -h localhost -U gw2optimizer $TEST_DB

# Verify
psql -h localhost -U gw2optimizer $TEST_DB -c "SELECT COUNT(*) FROM users;"

# Cleanup
dropdb -h localhost -U gw2optimizer $TEST_DB
```

---

## 🚨 INCIDENT RESPONSE

### **Severity Levels**
```
SEV1 (Critical): Service down, data loss
  Response: Immediate (< 5 min)
  
SEV2 (High): Degraded performance, partial outage
  Response: < 30 min
  
SEV3 (Medium): Non-critical feature broken
  Response: < 4 hours
  
SEV4 (Low): Minor bug, cosmetic issue
  Response: Next business day
```

### **Rollback Procedure**
```bash
# 1. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git checkout v0.4.0

# 3. Rebuild and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl http://localhost:8000/health
```

### **Emergency Contacts**
```
On-call: [Phone/Slack]
DevOps Lead: [Contact]
Database Admin: [Contact]
Security Team: [Contact]
```

---

## 📞 SUPPORT & ESCALATION

### **Logs Access**
```bash
# Application logs
docker-compose logs -f backend

# Error logs only
docker-compose logs backend | grep ERROR

# Specific time range
docker-compose logs --since 2025-11-16T14:00:00 backend
```

### **Debugging**
```bash
# Enter container
docker-compose exec backend bash

# Python shell
docker-compose exec backend python

# Database shell
docker-compose exec postgres psql -U gw2optimizer

# Redis shell
docker-compose exec redis redis-cli
```

---

**Dernière mise à jour**: 2025-11-16  
**Version**: v0.5.0  
**Responsable**: DevOps Team
