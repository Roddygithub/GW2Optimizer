# 🎯 Backend Coverage Roadmap: 29% → 60%

## 📊 État Actuel (Baseline)

**Coverage actuel**: ~29% (368 tests, beaucoup skipped sans Redis)

**Tests créés dans PR #80**:
- ✅ `test_api/test_auth_endpoints.py` (17 tests)
- ✅ `test_services/test_ai_services.py` (50+ tests)

## 🎯 Objectif: 60% Coverage

**Gap à combler**: +31 points de coverage

**Stratégie**: 4 sessions de 1-2h chacune

---

## 📋 Session 1: Auth & User Services (Target: +8%)

### Fichiers à couvrir
- `app/api/auth.py` (263 lignes, 0% → 80%)
- `app/services/user_service.py` (92 lignes, 29% → 85%)
- `app/core/security.py` (142 lignes, 0% → 70%)

### Tests à ajouter
```python
# test_api/test_auth_endpoints.py (DÉJÀ CRÉÉ, à exécuter avec Redis)
- ✅ Registration (success, duplicates, validation)
- ✅ Login (success, wrong password, inactive user)
- ✅ Profile (get, update, unauthorized)
- ✅ Password reset & change
- ✅ Token refresh
- ✅ Rate limiting

# test_services/test_user_service.py (NOUVEAU)
- User CRUD operations
- Email verification
- Password hashing/verification
- User preferences management
- Login history tracking
```

### Commandes
```bash
cd backend
poetry run pytest tests/test_api/test_auth_endpoints.py -v
poetry run pytest tests/test_services/test_user_service.py -v
poetry run coverage report --include="app/api/auth.py,app/services/user_service.py,app/core/security.py"
```

**Durée estimée**: 1-2h

---

## 📋 Session 2: Builds API & Services (Target: +10%)

### Fichiers à couvrir
- `app/api/builds.py` (endpoints builds, actuellement non testé)
- `app/services/build_service_db.py` (116 lignes, 15% → 70%)
- `app/models/build.py` (118 lignes, 100% → maintenir)

### Tests à ajouter
```python
# test_api/test_builds_endpoints.py (NOUVEAU)
- GET /api/v1/builds (list, pagination, filters)
- GET /api/v1/builds/{id} (success, not found)
- POST /api/v1/builds (create, validation errors)
- PUT /api/v1/builds/{id} (update, unauthorized)
- DELETE /api/v1/builds/{id} (delete, not found)
- GET /api/v1/builds/profession/{profession}
- POST /api/v1/builds/{id}/favorite

# test_services/test_build_service_db.py (NOUVEAU)
- create_build (success, duplicate)
- get_build (success, not found)
- list_builds (pagination, filters)
- update_build (success, not found)
- delete_build (success, cascade)
- search_builds (by profession, game_mode, tags)
```

### Commandes
```bash
poetry run pytest tests/test_api/test_builds_endpoints.py -v
poetry run pytest tests/test_services/test_build_service_db.py -v
poetry run coverage report --include="app/api/builds.py,app/services/build_service_db.py"
```

**Durée estimée**: 1.5-2h

---

## 📋 Session 3: Teams API & Services (Target: +8%)

### Fichiers à couvrir
- `app/api/teams.py` (endpoints teams)
- `app/services/team_service_db.py` (189 lignes, 11% → 65%)

### Tests à ajouter
```python
# test_api/test_teams_endpoints.py (NOUVEAU)
- GET /api/v1/teams (list, pagination)
- GET /api/v1/teams/{id} (success, not found)
- POST /api/v1/teams (create, validation)
- PUT /api/v1/teams/{id} (update)
- DELETE /api/v1/teams/{id} (delete)
- POST /api/v1/teams/compose (AI composition)
- GET /api/v1/teams/{id}/synergy (synergy analysis)

# test_services/test_team_service_db.py (NOUVEAU)
- create_team (success, validation)
- get_team (success, not found)
- list_teams (pagination, filters)
- update_team (success, not found)
- delete_team (success, cascade)
- add_member (success, duplicate)
- remove_member (success, not found)
```

### Commandes
```bash
poetry run pytest tests/test_api/test_teams_endpoints.py -v
poetry run pytest tests/test_services/test_team_service_db.py -v
poetry run coverage report --include="app/api/teams.py,app/services/team_service_db.py"
```

**Durée estimée**: 1.5h

---

## 📋 Session 4: Critical Paths & Edge Cases (Target: +5%)

### Fichiers à couvrir
- `app/services/gw2_api_client.py` (123 lignes, 21% → 60%)
- `app/services/mistral_ai.py` (62 lignes, 27% → 70%)
- `app/middleware/performance.py` (68 lignes, 0% → 80%)
- Error handlers & edge cases

### Tests à ajouter
```python
# test_services/test_gw2_api_client.py (NOUVEAU)
- fetch_professions (success, API error, timeout)
- fetch_skills (success, cache hit)
- fetch_traits (success, rate limit)
- Error handling & retries

# test_services/test_mistral_ai.py (AMÉLIORER EXISTANT)
- More error scenarios
- Rate limiting
- Token counting
- Fallback strategies

# test_middleware/test_performance.py (NOUVEAU)
- X-Response-Time header
- Slow request logging
- Metrics tracking

# test_error_handlers.py (NOUVEAU)
- 404 handler
- 500 handler
- Validation errors
- Custom exceptions
```

### Commandes
```bash
poetry run pytest tests/test_services/test_gw2_api_client.py -v
poetry run pytest tests/test_middleware/ -v
poetry run pytest tests/test_error_handlers.py -v
poetry run coverage report
```

**Durée estimée**: 1-2h

---

## 🚀 Exécution du Plan

### Prérequis
```bash
# 1. Démarrer Redis (pour éviter tests skipped)
docker run -d -p 6379:6379 redis:alpine

# OU utiliser docker-compose
docker-compose -f docker-compose.dev.yml up -d redis

# 2. Vérifier connexion
redis-cli ping  # Devrait retourner PONG
```

### Workflow par Session

```bash
# 1. Créer branche
git checkout -b feature/coverage-session-X

# 2. Écrire tests
# ... coder les tests ...

# 3. Exécuter tests
poetry run pytest tests/test_XXX -v

# 4. Vérifier coverage
poetry run coverage run -m pytest
poetry run coverage report --show-missing

# 5. Générer rapport HTML
poetry run coverage html
open htmlcov/index.html

# 6. Commit + push
git add tests/
git commit -m "test: Add coverage for XXX (+Y%)"
git push -u origin feature/coverage-session-X

# 7. Créer PR
gh pr create --title "test: Coverage Session X - XXX (+Y%)" --base main
```

### Validation Finale

```bash
# Après toutes les sessions
poetry run pytest --cov=app --cov-report=term --cov-report=html
poetry run coverage report --fail-under=60

# Si >= 60%, succès ! 🎉
```

---

## 📊 Suivi de Progression

| Session | Fichiers | Tests | Coverage Gain | Status |
|---------|----------|-------|---------------|--------|
| 1. Auth & User | 3 | ~30 | +8% | ⏳ Pending |
| 2. Builds | 2 | ~25 | +10% | ⏳ Pending |
| 3. Teams | 2 | ~20 | +8% | ⏳ Pending |
| 4. Critical Paths | 4 | ~15 | +5% | ⏳ Pending |
| **TOTAL** | **11** | **~90** | **+31%** | **🎯 60%** |

---

## 🎯 Priorités

### Must-Have (pour atteindre 60%)
1. ✅ Auth endpoints (déjà créé, à exécuter)
2. 🔴 Builds CRUD
3. 🔴 Teams CRUD
4. 🔴 User service

### Nice-to-Have (pour dépasser 60%)
5. 🟡 AI services (déjà partiellement créé)
6. 🟡 GW2 API client
7. 🟡 Middleware
8. 🟡 Error handlers

---

## 🛠️ Outils Utiles

### Identifier les gaps
```bash
# Voir fichiers avec faible coverage
poetry run coverage report --show-missing | grep -E "^app/" | sort -k4 -n

# Voir lignes non couvertes d'un fichier
poetry run coverage report --show-missing --include="app/api/builds.py"

# Générer rapport HTML interactif
poetry run coverage html
open htmlcov/index.html  # Cliquer sur fichiers rouges
```

### Déboguer tests
```bash
# Mode verbose
poetry run pytest tests/test_XXX.py -v

# Avec logs
poetry run pytest tests/test_XXX.py -v -s

# Un seul test
poetry run pytest tests/test_XXX.py::test_function_name -v

# Avec debugger
poetry run pytest tests/test_XXX.py --pdb
```

---

## 📝 Notes

- **Redis requis** : Beaucoup de tests sont skipped sans Redis. Démarrer Redis avant les sessions.
- **DB isolation** : Tests utilisent SQLite en mémoire (voir `conftest.py`)
- **Fixtures** : Réutiliser fixtures existantes (`client`, `auth_headers`, `test_user`, `db_session`)
- **Mocking** : Mocker appels externes (GW2 API, Mistral AI) pour tests rapides
- **Async** : Utiliser `@pytest.mark.asyncio` pour tests async

---

## 🎉 Succès Attendu

Après les 4 sessions :
- ✅ Coverage backend : **60%+**
- ✅ ~90 nouveaux tests
- ✅ Tous les endpoints critiques couverts
- ✅ Services métier testés
- ✅ Error paths validés
- ✅ CI verte avec coverage check

**Temps total estimé** : 5-7 heures réparties sur 4 sessions
