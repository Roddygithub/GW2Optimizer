# 🔄 GW2Optimizer CI/CD Workflows

## 📋 Workflows Disponibles

### 1. **CI/CD Pipeline** (`ci.yml`)
**Déclencheur**: Push sur toutes les branches

**Étapes**:
- ✅ Lint & Format (Black, Flake8)
- ✅ Build Backend + Frontend
- ✅ Tests Unitaires (32 tests)
- ✅ Tests API (27 tests)
- ✅ Tests Intégration (20 tests)

**Services**:
- PostgreSQL 14
- Redis

**Status**: ✅ Production Ready

---

### 2. **Real Conditions E2E Test** (`test_real_conditions.yml`)
**Déclencheur**: Push sur `main` et `dev` + Manuel

**Étapes**:
- ✅ Backend + Frontend startup
- ✅ Health checks
- ✅ Auth flow (register, login, protected)
- ✅ Build creation
- ✅ GW2 API integration
- ✅ Mistral AI integration

**Secrets Requis**:
- `MISTRAL_API_KEY`
- `GW2_API_KEY`

**Artifacts**:
- Test report (30 jours)
- Logs backend/frontend (30 jours)

**Status**: 🆕 Nouveau (v2.6.0)

---

## 🔐 Configuration Secrets

Pour configurer les secrets GitHub:

```bash
# 1. Va dans Settings → Secrets and variables → Actions
# 2. Clique sur "New repository secret"
# 3. Ajoute:
#    - MISTRAL_API_KEY (https://console.mistral.ai)
#    - GW2_API_KEY (depuis le jeu GW2)
```

Voir [E2E_REAL_CONDITIONS_SETUP.md](../../docs/E2E_REAL_CONDITIONS_SETUP.md) pour guide complet.

---

## 📊 Métriques Actuelles

| Workflow | Tests | Pass Rate | Durée |
|----------|-------|-----------|-------|
| **CI/CD Pipeline** | 79 | 95% | ~4 min |
| **E2E Real Conditions** | 7+ | 100% | ~2 min |

---

## 🎯 Utilisation

### Lancer manuellement un workflow

1. Va dans **Actions**
2. Sélectionne le workflow
3. Clique sur **Run workflow**
4. Choisis la branche
5. Clique sur **Run workflow**

### Voir les résultats

1. Va dans **Actions**
2. Clique sur le run
3. Clique sur le job (ex: "Test Backend")
4. Consulte les logs

### Télécharger les artifacts

1. Dans le run terminé
2. Scroll vers **Artifacts**
3. Clique sur le nom pour télécharger

---

## 🔧 Maintenance

### Ajouter un nouveau workflow

1. Crée `nouveau_workflow.yml` dans `.github/workflows/`
2. Définis le déclencheur (`on:`)
3. Ajoute les jobs et steps
4. Commit et push

### Modifier un workflow existant

1. Édite le fichier `.yml`
2. Commit et push
3. Le workflow sera automatiquement mis à jour

---

## 📈 Historique

| Version | Date | Changement |
|---------|------|------------|
| **v2.6.0** | 2025-10-22 | + Real Conditions E2E Test |
| **v2.5.0** | 2025-10-22 | PostgreSQL integration |
| **v2.4.0** | 2025-10-21 | SQLite tests isolation |

---

**Pour plus d'infos**: Voir `/reports/ci/` pour les rapports détaillés.
