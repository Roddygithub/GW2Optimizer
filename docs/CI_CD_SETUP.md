# Configuration CI/CD - GW2Optimizer

## 📋 Configuration des secrets GitHub

Pour que les workflows GitHub Actions fonctionnent correctement, vous devez configurer les secrets suivants dans votre repository.

### Accès aux secrets

1. Allez sur votre repository GitHub
2. Cliquez sur **Settings** → **Secrets and variables** → **Actions**
3. Cliquez sur **New repository secret**

### Secrets requis

#### Pour le workflow CI (`ci.yml`)

| Secret | Description | Exemple |
|--------|-------------|---------|
| `CODECOV_TOKEN` | Token d'authentification Codecov | `abc123...` |

**Note** : Le token Codecov est optionnel. Si vous ne l'avez pas, le workflow continuera mais ne uploadera pas la couverture.

#### Pour le workflow Learning Pipeline (`scheduled-learning.yml`)

| Secret | Description | Exemple |
|--------|-------------|---------|
| `DB_USER` | Utilisateur PostgreSQL | `gw2optimizer` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | `secure_password_123` |
| `DB_NAME` | Nom de la base de données | `gw2optimizer_prod` |
| `DATABASE_URL` | URL complète de connexion | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | URL de connexion Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Clé secrète JWT | Générer avec `openssl rand -hex 32` |

### Génération des secrets

#### SECRET_KEY

```bash
# Générer une clé secrète sécurisée
openssl rand -hex 32
```

#### DATABASE_URL

Format : `postgresql://[user]:[password]@[host]:[port]/[database]`

Exemple :
```
postgresql://gw2optimizer:mypassword@db.example.com:5432/gw2optimizer_prod
```

#### REDIS_URL

Format : `redis://[host]:[port]/[db_number]`

Exemple :
```
redis://cache.example.com:6379/0
```

## 🔧 Configuration Codecov

### Étape 1 : Créer un compte Codecov

1. Allez sur [codecov.io](https://codecov.io)
2. Connectez-vous avec votre compte GitHub
3. Autorisez Codecov à accéder à vos repositories

### Étape 2 : Activer le repository

1. Dans Codecov, cliquez sur **Add new repository**
2. Sélectionnez `GW2Optimizer`
3. Copiez le token généré

### Étape 3 : Ajouter le token à GitHub

1. Dans GitHub, allez dans **Settings** → **Secrets**
2. Créez un nouveau secret nommé `CODECOV_TOKEN`
3. Collez le token copié depuis Codecov

### Étape 4 : Configuration codecov.yml (optionnel)

Créez un fichier `.codecov.yml` à la racine du projet :

```yaml
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 5%
    patch:
      default:
        target: 80%

comment:
  layout: "reach, diff, flags, files"
  behavior: default
  require_changes: false
```

## 🚀 Workflows disponibles

### 1. CI/CD Pipeline (`ci.yml`)

**Déclenchement** :
- Push sur `main` ou `dev`
- Pull requests vers `main` ou `dev`

**Étapes** :
1. **Lint Backend** : Black, Flake8, isort, MyPy
2. **Test Backend** : Tests unitaires, API, intégration avec PostgreSQL + Redis
3. **Upload Coverage** : Envoi du rapport vers Codecov
4. **Build Status** : Vérification finale

**Services** :
- PostgreSQL 14
- Redis 7

### 2. Scheduled Learning Pipeline (`scheduled-learning.yml`)

**Déclenchement** :
- Automatique : Tous les dimanches à 00:00 UTC
- Manuel : Via l'interface GitHub Actions

**Étapes** :
1. Collecte des données d'apprentissage
2. Traitement des données
3. Génération des statistiques
4. Archivage des données (90 jours)
5. Notification en cas d'échec

## 📊 Badges de statut

Ajoutez ces badges à votre README.md :

### Badge CI/CD

```markdown
[![CI/CD](https://github.com/[username]/GW2Optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/[username]/GW2Optimizer/actions/workflows/ci.yml)
```

### Badge Codecov

```markdown
[![codecov](https://codecov.io/gh/[username]/GW2Optimizer/branch/main/graph/badge.svg)](https://codecov.io/gh/[username]/GW2Optimizer)
```

Remplacez `[username]` par votre nom d'utilisateur GitHub.

## 🔍 Vérification de la configuration

### Tester localement avec act

```bash
# Installer act
brew install act  # macOS
# ou
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Lister les workflows
act -l

# Exécuter le workflow CI
act -j lint-backend

# Exécuter avec secrets
act -j test-backend --secret-file .secrets
```

### Format du fichier .secrets

```env
CODECOV_TOKEN=your_token_here
DB_USER=test
DB_PASSWORD=test
DB_NAME=gw2optimizer_test
DATABASE_URL=postgresql://test:test@localhost:5432/gw2optimizer_test
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=test_secret_key_for_local_testing_only
```

## 🐛 Dépannage

### Le workflow échoue avec "Secret not found"

**Solution** : Vérifiez que tous les secrets requis sont configurés dans GitHub Settings.

### Le workflow échoue sur "Upload coverage"

**Solution** : 
1. Vérifiez que `CODECOV_TOKEN` est configuré
2. Ou ajoutez `continue-on-error: true` à l'étape d'upload

### Les tests échouent avec "Connection refused"

**Solution** : Les services PostgreSQL et Redis ne sont pas démarrés. Vérifiez la configuration des services dans le workflow.

### Le workflow est lent

**Solutions** :
1. Utiliser le cache pip : `cache: 'pip'` dans setup-python
2. Paralléliser les tests : `pytest -n auto`
3. Réduire le nombre d'étapes de test

## 📝 Bonnes pratiques

### Sécurité

- ✅ Ne jamais commiter de secrets dans le code
- ✅ Utiliser des secrets GitHub pour les données sensibles
- ✅ Générer des clés secrètes fortes
- ✅ Rotation régulière des secrets
- ✅ Utiliser des secrets différents pour dev/staging/prod

### Performance

- ✅ Utiliser le cache pour les dépendances
- ✅ Paralléliser les tests quand possible
- ✅ Limiter le nombre de services Docker
- ✅ Nettoyer les artefacts anciens

### Maintenance

- ✅ Mettre à jour régulièrement les actions GitHub
- ✅ Surveiller les dépréciations
- ✅ Documenter les changements de configuration
- ✅ Tester les workflows avant de merger

## 🔗 Ressources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [act - Local GitHub Actions](https://github.com/nektos/act)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)

## 📧 Support

Pour toute question sur la configuration CI/CD :
1. Consulter cette documentation
2. Vérifier les logs des workflows dans GitHub Actions
3. Créer une issue avec le label `ci/cd`

---

**Dernière mise à jour** : 2024-01-20  
**Version** : 1.2.0
