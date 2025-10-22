# 🧪 QUICK TEST GUIDE - GW2Optimizer v2.9.0

**Date**: 2025-10-23 00:50 UTC+02:00  
**Status**: ✅ Ready to Test

---

## 🚀 TESTS RAPIDES (5 MINUTES)

### 1. Test Sentry Backend (2 min)

```bash
# Terminal 1: Démarrer backend
cd backend
uvicorn app.main:app --reload
```

**Logs attendus**:
```
📊 Sentry error tracking initialized (tracing + profiling enabled)
📈 Prometheus metrics endpoint enabled at /metrics
🐛 Sentry debug endpoint enabled at /api/v1/sentry-debug
```

```bash
# Terminal 2: Tester Sentry
curl http://localhost:8000/api/v1/sentry-debug
```

**Résultat attendu**:
```json
{
  "detail": "Internal Server Error"
}
```

**Vérifier dans Sentry** (https://sentry.io):
- ✅ Issues → "ZeroDivisionError"
- ✅ Performance → Transaction "/api/v1/sentry-debug"
- ✅ Profiling → Profile visible

---

### 2. Test Prometheus Metrics (1 min)

```bash
curl http://localhost:8000/metrics
```

**Résultat attendu**:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/sentry-debug"} 1.0
...
```

---

### 3. Test Frontend Sentry (2 min)

```bash
# Terminal 3: Installer et démarrer frontend
cd frontend
npm install
npm run dev
```

**Ouvrir**: http://localhost:5173

**Test**:
1. Chercher le bouton rouge "🐛 Test Sentry" (bottom-right)
2. Cliquer dessus
3. Voir l'erreur dans la console

**Vérifier dans Sentry**:
- ✅ Issues → "This is your first Sentry error! 🎉"
- ✅ Logs → Message "User triggered test error"

---

## 🔧 CONFIGURATION COMPLÈTE (10 MINUTES)

### Backend Configuration

**Fichier**: `backend/.env`

```bash
# Copier .env.example
cp backend/.env.example backend/.env

# Vérifier la configuration
cat backend/.env | grep SENTRY_DSN
```

**DSN Backend**:
```
SENTRY_DSN=https://d7067f5675913b468876ace2ce7cfefd@o4510235525120000.ingest.de.sentry.io/4510235538489424
```

---

### Frontend Configuration

**Fichier**: `frontend/.env.production`

```bash
# Copier .env.production.example
cp frontend/.env.production.example frontend/.env.production

# Vérifier la configuration
cat frontend/.env.production | grep VITE_SENTRY_DSN
```

**DSN Frontend**:
```
VITE_SENTRY_DSN=https://bdd0ff8259b4cbc7214e79260ad04614@o4510235525120000.ingest.de.sentry.io/4510235571847248
```

---

## 📊 MONITORING STACK (5 MINUTES)

### Démarrer Prometheus + Grafana

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

**Accès**:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

**Vérifier**:
```bash
# Status des containers
docker-compose -f docker-compose.monitoring.yml ps

# Logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

---

## 🌐 TEST E2E REAL CONDITIONS (3 MINUTES)

### Lancer CI Supervisor

```bash
cd backend
python scripts/ci_supervisor_v29.py
```

**Résultat attendu**:
```
🚀 CI SUPERVISOR v2.9.0 - PRODUCTION READY + E2E REAL
═══════════════════════════════════════════════════
🧪 Running pytest backend tests...
✅ SUCCESS: All critical tests passed!

🌐 Running E2E Real Conditions Test...
📡 Fetching live WvW data from GW2 API...
🤖 Generating team composition with Mistral AI...
✅ Real E2E test completed successfully
✅ E2E report generated: reports/e2e_real_conditions/team_report_*.json
```

**Vérifier rapports**:
```bash
ls -la reports/e2e_real_conditions/
cat reports/e2e_real_conditions/team_report_*.json
```

---

## ✅ CHECKLIST COMPLÈTE

### Backend ✅
- [ ] Sentry initialisé (logs: "📊 Sentry error tracking initialized")
- [ ] Prometheus metrics exposé (curl /metrics)
- [ ] Endpoint debug fonctionne (curl /api/v1/sentry-debug)
- [ ] Erreur visible dans Sentry Issues
- [ ] Transaction visible dans Sentry Performance
- [ ] Profile visible dans Sentry Profiling

### Frontend ✅
- [ ] npm install réussi
- [ ] npm run dev démarre
- [ ] Bouton "Test Sentry" visible (dev only)
- [ ] Click bouton → erreur dans console
- [ ] Erreur visible dans Sentry Issues
- [ ] Log visible dans Sentry Logs

### Monitoring ✅
- [ ] Docker Compose démarre
- [ ] Grafana accessible (localhost:3000)
- [ ] Prometheus accessible (localhost:9090)
- [ ] Métriques visibles dans Prometheus

### E2E ✅
- [ ] CI Supervisor s'exécute
- [ ] Tests backend passent
- [ ] E2E test s'exécute
- [ ] Rapports JSON/YAML générés

---

## 🐛 TROUBLESHOOTING

### Sentry Backend ne fonctionne pas

**Problème**: Pas de logs "Sentry initialized"

**Solutions**:
```bash
# Vérifier .env
cat backend/.env | grep SENTRY_DSN

# Vérifier TESTING=False
cat backend/.env | grep TESTING

# Réinstaller sentry-sdk
pip install "sentry-sdk[fastapi]"
```

---

### Sentry Frontend ne fonctionne pas

**Problème**: Bouton test non visible

**Solutions**:
```bash
# Vérifier mode dev (pas prod)
npm run dev  # Pas npm run build

# Installer @sentry/react
npm install @sentry/react

# Vérifier .env.production
cat frontend/.env.production | grep VITE_SENTRY_DSN
```

---

### Prometheus metrics vides

**Problème**: curl /metrics → 404

**Solutions**:
```bash
# Vérifier TESTING=False
cat backend/.env | grep TESTING

# Réinstaller prometheus
pip install prometheus-fastapi-instrumentator

# Redémarrer backend
uvicorn app.main:app --reload
```

---

### E2E test échoue

**Problème**: "Real E2E failed, using fallback"

**Solutions**:
```bash
# Normal si API keys non configurées
# Vérifier fallback data dans rapport JSON

# Pour activer vraiment:
# 1. Ajouter GW2_API_KEY dans .env
# 2. Ajouter MISTRAL_API_KEY dans .env
# 3. Re-run CI Supervisor
```

---

## 📈 MÉTRIQUES DE SUCCÈS

### Backend
```
✅ Sentry initialized: OUI
✅ Prometheus /metrics: 200 OK
✅ Debug endpoint: 500 (expected)
✅ Sentry Issues: 1+ error
✅ Sentry Performance: 1+ transaction
✅ Sentry Profiling: 1+ profile
```

### Frontend
```
✅ npm install: SUCCESS
✅ npm run dev: RUNNING
✅ Test button: VISIBLE
✅ Click test: ERROR (expected)
✅ Sentry Issues: 1+ error
✅ Sentry Logs: 1+ log
```

### Monitoring
```
✅ Grafana: UP (localhost:3000)
✅ Prometheus: UP (localhost:9090)
✅ Metrics: SCRAPED
```

### E2E
```
✅ Backend tests: GREEN
✅ E2E test: EXECUTED
✅ Reports: GENERATED
```

---

## 🎯 PROCHAINES ÉTAPES

### Après Tests Réussis

1. **Configurer API Keys**
   ```bash
   # backend/.env
   GW2_API_KEY=your-key
   MISTRAL_API_KEY=your-key
   ```

2. **Créer Grafana Dashboards**
   - API response times
   - Error rates
   - Request counts

3. **Configurer Alertes Sentry**
   - Email notifications
   - Slack integration

4. **Déployer Production**
   - Configure environment
   - Setup SSL
   - Deploy!

---

## 📝 COMMANDES UTILES

### Backend
```bash
# Démarrer
uvicorn app.main:app --reload

# Tester Sentry
curl http://localhost:8000/api/v1/sentry-debug

# Voir métriques
curl http://localhost:8000/metrics

# Voir logs
tail -f logs/gw2optimizer.log
```

### Frontend
```bash
# Installer
npm install

# Dev
npm run dev

# Build
npm run build

# Preview
npm run preview
```

### Monitoring
```bash
# Démarrer
docker-compose -f docker-compose.monitoring.yml up -d

# Status
docker-compose -f docker-compose.monitoring.yml ps

# Logs
docker-compose -f docker-compose.monitoring.yml logs -f

# Arrêter
docker-compose -f docker-compose.monitoring.yml down
```

### E2E
```bash
# Lancer CI Supervisor
python backend/scripts/ci_supervisor_v29.py

# Voir rapports
ls -la reports/e2e_real_conditions/
cat reports/e2e_real_conditions/team_report_*.json
```

---

## 🎉 CONCLUSION

**Si tous les tests passent**: ✅ GW2Optimizer v2.9.0 est PRODUCTION READY!

**Durée totale des tests**: ~15 minutes

**Prochaine étape**: Déploiement production 🚀

---

**Last Updated**: 2025-10-23 00:50 UTC+02:00  
**Version**: v2.9.0  
**Status**: Ready to Test
