# 🚀 DEPLOYMENT GUIDE - GW2Optimizer v3.0.0

**Date**: 2025-10-23 01:10 UTC+02:00  
**Version**: v3.0.0  
**Status**: ✅ PRODUCTION READY

---

## 🎯 OVERVIEW

Ce guide couvre le déploiement complet de GW2Optimizer v3.0.0 avec:
- Backend FastAPI
- Frontend React
- Monitoring Stack (Prometheus + Grafana)
- Error Tracking (Sentry)
- AI Services (Mistral + GW2 API)

---

## 📋 PRÉREQUIS

### Système
```
OS: Linux (Ubuntu 22.04+ recommended)
RAM: 4GB minimum, 8GB recommended
CPU: 2 cores minimum, 4 cores recommended
Disk: 20GB minimum, 50GB recommended
```

### Software
```
Python: 3.11+
Node.js: 20+
PostgreSQL: 14+
Redis: 7+
Docker: 24+
Docker Compose: 2+
```

### API Keys
```
SENTRY_DSN (backend): https://d7067f5675913b468876ace2ce7cfefd@...
VITE_SENTRY_DSN (frontend): https://bdd0ff8259b4cbc7214e79260ad04614@...
GW2_API_KEY: From https://account.arena.net/applications
MISTRAL_API_KEY: From https://console.mistral.ai/
```

---

## 🔧 INSTALLATION

### 1. Clone Repository

```bash
git clone https://github.com/Roddygithub/GW2Optimizer.git
cd GW2Optimizer
git checkout v3.0.0
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit configuration
```

**Configuration (.env)**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/gw2optimizer

# Monitoring
SENTRY_DSN=https://d7067f5675913b468876ace2ce7cfefd@...
PROMETHEUS_ENABLED=True

# External APIs
GW2_API_KEY=your-gw2-api-key
MISTRAL_API_KEY=your-mistral-api-key

# Redis
REDIS_ENABLED=True
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Environment
ENVIRONMENT=production
DEBUG=False
TESTING=False
```

```bash
# Initialize database
alembic upgrade head

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.production.example .env.production
nano .env.production  # Edit configuration
```

**Configuration (.env.production)**:
```bash
# Sentry
VITE_SENTRY_DSN=https://bdd0ff8259b4cbc7214e79260ad04614@...

# API
VITE_API_URL=http://localhost:8000
```

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Or serve with nginx (recommended)
# Copy dist/ to /var/www/gw2optimizer
```

### 4. Monitoring Stack

```bash
# Start Prometheus + Grafana
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps

# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

---

## 🧪 VALIDATION

### Backend Tests

```bash
cd backend

# Critical tests
pytest -m 'not legacy' -v

# All tests
pytest -v

# Coverage
pytest --cov=app --cov-report=html
```

**Expected**: 100/104 tests passing (96%)

### Frontend Tests

```bash
cd frontend

# All tests
npm test -- --run

# Coverage
npm run test:coverage -- --run
```

**Expected**: 51/51 tests passing (~60% coverage)

### Monitoring Tests

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Sentry backend
curl http://localhost:8000/api/v1/sentry-debug

# Health check
curl http://localhost:8000/health
```

### AI Optimizer Test

```bash
cd backend

# Run real test
python scripts/test_real_ai.py

# Check reports
ls -la ../reports/REAL_AI_TEAM_TEST.*
```

---

## 🌐 PRODUCTION DEPLOYMENT

### Option 1: Docker (Recommended)

**Create docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - SENTRY_DSN=...
      - GW2_API_KEY=...
      - MISTRAL_API_KEY=...
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=gw2optimizer
      - POSTGRES_USER=gw2user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_password
    restart: unless-stopped

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

**Deploy**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Systemd Services

**Backend Service** (`/etc/systemd/system/gw2optimizer-backend.service`):
```ini
[Unit]
Description=GW2Optimizer Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/gw2optimizer/backend
Environment="PATH=/opt/gw2optimizer/backend/venv/bin"
ExecStart=/opt/gw2optimizer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend with Nginx** (`/etc/nginx/sites-available/gw2optimizer`):
```nginx
server {
    listen 80;
    server_name gw2optimizer.com;

    root /var/www/gw2optimizer;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Enable services**:
```bash
sudo systemctl enable gw2optimizer-backend
sudo systemctl start gw2optimizer-backend
sudo systemctl enable nginx
sudo systemctl restart nginx
```

---

## 📊 MONITORING

### Grafana Dashboard

1. **Access Grafana**: http://localhost:3000
2. **Login**: admin / admin
3. **Import Dashboard**:
   - Go to Dashboards → Import
   - Upload `monitoring/grafana/dashboards/gw2optimizer_dashboard.json`
   - Select Prometheus datasource

### Prometheus Queries

**API Request Rate**:
```promql
rate(http_requests_total[5m])
```

**Response Time (p95)**:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Error Rate**:
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### Sentry Configuration

**Backend**: Already configured in `.env`

**Frontend**: Already configured in `.env.production`

**Verify**:
- Backend: http://localhost:8000/api/v1/sentry-debug
- Frontend: Click "Test Sentry" button (dev mode)

---

## 🔒 SECURITY

### SSL/TLS

**With Let's Encrypt**:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d gw2optimizer.com
```

### Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### Environment Variables

**Never commit**:
- `.env` files
- API keys
- Passwords
- Secrets

**Use**:
- GitHub Secrets (CI/CD)
- Environment variables (production)
- Vault (advanced)

---

## 🔄 CI/CD

### GitHub Actions

**Workflow** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/gw2optimizer
            git pull origin main
            docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📈 SCALING

### Horizontal Scaling

**Load Balancer** (Nginx):
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api {
        proxy_pass http://backend;
    }
}
```

### Database Scaling

**Read Replicas**:
```python
# app/db/session.py
SQLALCHEMY_DATABASE_URI_READ = "postgresql+asyncpg://..."
```

**Connection Pooling**:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

### Caching

**Redis Cluster**:
```yaml
redis:
  image: redis:7-cluster
  environment:
    - REDIS_CLUSTER_ENABLED=yes
```

---

## 🐛 TROUBLESHOOTING

### Backend Won't Start

**Check logs**:
```bash
journalctl -u gw2optimizer-backend -f
```

**Common issues**:
- Database connection: Check `DATABASE_URL`
- Redis connection: Check `REDIS_URL`
- Port in use: `lsof -i :8000`

### Frontend Build Fails

**Check Node version**:
```bash
node --version  # Should be 20+
```

**Clear cache**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Monitoring Not Working

**Check Docker**:
```bash
docker-compose -f docker-compose.monitoring.yml ps
docker-compose -f docker-compose.monitoring.yml logs
```

**Check Prometheus targets**:
```bash
curl http://localhost:9090/api/v1/targets
```

---

## 📚 ADDITIONAL RESOURCES

### Documentation
- [SENTRY_SETUP.md](./SENTRY_SETUP.md) - Sentry configuration
- [QUICK_TEST_GUIDE.md](./QUICK_TEST_GUIDE.md) - Testing guide
- [MISSION_v3.0_FINAL_REPORT.md](../reports/MISSION_v3.0_FINAL_REPORT.md) - Final report

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Support
- GitHub Issues: https://github.com/Roddygithub/GW2Optimizer/issues
- Documentation: https://github.com/Roddygithub/GW2Optimizer/wiki

---

## ✅ POST-DEPLOYMENT CHECKLIST

### Immediate
- [ ] Backend accessible
- [ ] Frontend accessible
- [ ] Database connected
- [ ] Redis connected
- [ ] Monitoring operational
- [ ] Sentry receiving events

### First Hour
- [ ] Run health checks
- [ ] Verify metrics in Grafana
- [ ] Test AI optimizer endpoint
- [ ] Check error rates
- [ ] Monitor performance

### First Day
- [ ] Review Sentry issues
- [ ] Analyze Grafana dashboards
- [ ] Check database performance
- [ ] Verify cache hit rates
- [ ] Test all endpoints

### First Week
- [ ] Setup alerting
- [ ] Configure backups
- [ ] Document runbooks
- [ ] Train team
- [ ] Plan scaling

---

## 🎉 CONCLUSION

**GW2Optimizer v3.0.0 is ready for production deployment!**

Follow this guide for a smooth deployment experience.

For questions or issues, refer to the documentation or create a GitHub issue.

---

**Last Updated**: 2025-10-23 01:10 UTC+02:00  
**Version**: v3.0.0  
**Status**: Production Ready 🚀
