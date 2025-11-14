# Configuration des secrets GitHub

## Secrets requis pour security.yml

### 1. SEMGREP_APP_TOKEN (SAST scanning)

**Obtenir le token** :
1. Créer un compte sur https://semgrep.dev
2. Aller dans Settings → Tokens
3. Créer un token « GitHub Actions »

**Configurer dans GitHub** :
```bash
# Repository → Settings → Secrets and variables → Actions
# New repository secret :
Name: SEMGREP_APP_TOKEN
Value: <coller le token>
```

**Alternative (open-source)** : Utiliser Semgrep sans token

YAML
```yaml
- name: Semgrep
  uses: semgrep/semgrep-action@v1
  env:
    SEMGREP_RULES: auto  # Règles publiques seulement
  # Ne pas utiliser SEMGREP_APP_TOKEN
```

### 2. GITLEAKS_LICENSE_KEY (secrets scanning)

Option A : Version gratuite (recommandée)

YAML
```yaml
- name: Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    # Pas de licence pour la version gratuite
```

Option B : Version entreprise

Acheter une licence sur https://gitleaks.io

Configurer :
```bash
Name: GITLEAKS_LICENSE_KEY
Value: <licence-key>
```

### 3. CODECOV_TOKEN (optionnel - coverage reporting)

**Obtenir le token** :
1. Créer un compte sur https://codecov.io
2. Lier votre repository GitHub
3. Copier le token du repository

**Configurer** :
```bash
Name: CODECOV_TOKEN
Value: <token-codecov>
```

**Utilisation dans CI** :
```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage.xml
```

## Secrets production (backend)

### SECRET_KEY (JWT signing)
**Générer** :
```bash
openssl rand -hex 32
```
**Configurer** :
```bash
# En production (jamais dans .env committé)
Name: SECRET_KEY
Value: <clé-générée-32-bytes>
```

### DATABASE_URL
**Format** :
```
postgresql://user:password@host:port/database
```
**Exemple production** :
```bash
Name: DATABASE_URL
Value: postgresql://prod_user:STRONG_PASSWORD@db.example.com:5432/gamebuilder_prod
```

### REDIS_URL
**Format** :
```
redis://[username:password@]host:port/db
```
**Exemple production** :
```bash
Name: REDIS_URL
Value: redis://:REDIS_PASSWORD@redis.example.com:6379/0
```

## Vérification

Tester que les secrets sont bien configurés :
```bash
git push origin main
# Vérifier dans GitHub Actions que security.yml s’exécute et passe
```

### Secrets critiques :
- ✅ SECRET_KEY (backend)
- ✅ DATABASE_URL (production)
- ✅ REDIS_URL (production)
- ⚠️ SEMGREP_APP_TOKEN (optionnel)
- ⚠️ GITLEAKS_LICENSE_KEY (optionnel)
- ⚠️ CODECOV_TOKEN (optionnel)

### Rotation des secrets :
- SECRET_KEY : tous les 90 jours
- DATABASE_URL : lors de changement infra
- Tokens API : selon politique du fournisseur

FIN du fichier.
