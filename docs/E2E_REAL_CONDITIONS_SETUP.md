# 🧪 E2E Real Conditions Test - Setup Guide

## 📋 Overview

Le workflow **Real Conditions E2E Test** exécute des tests complets en conditions réelles de production avec:
- ✅ Mistral AI pour génération de builds intelligents
- ✅ API Guild Wars 2 pour validation des données
- ✅ Backend FastAPI + Frontend React
- ✅ Tests d'authentification et autorisation
- ✅ Création et gestion de builds

## 🔐 Configuration des Secrets GitHub

### 1. Accéder aux Secrets

1. Va sur ton dépôt GitHub: `https://github.com/Roddygithub/GW2Optimizer`
2. Clique sur **Settings** (dans le menu du dépôt)
3. Dans le menu latéral, clique sur **Secrets and variables** → **Actions**
4. Clique sur **New repository secret**

### 2. Ajouter MISTRAL_API_KEY

**Nom**: `MISTRAL_API_KEY`  
**Valeur**: Ta clé API Mistral

#### Comment obtenir ta clé Mistral AI:
1. Va sur https://console.mistral.ai/
2. Créer un compte (gratuit)
3. Va dans **API Keys**
4. Clique sur **Create new key**
5. Copie la clé (format: `xxx...`)

**Important**: La clé gratuite de Mistral permet:
- ✅ 5$ de crédits gratuits
- ✅ ~1000 requêtes avec `mistral-small-latest`
- ✅ Parfait pour tests CI/CD

### 3. Ajouter GW2_API_KEY

**Nom**: `GW2_API_KEY`  
**Valeur**: Ta clé API Guild Wars 2

#### Comment obtenir ta clé GW2 API:
1. Lance Guild Wars 2
2. Va dans les paramètres du jeu
3. Ouvre le panneau **API Keys**
4. Crée une nouvelle clé avec permissions:
   - ✅ `account` (lecture)
   - ✅ `characters` (lecture)
   - ✅ `builds` (lecture)
   - ✅ `inventories` (lecture)
5. Copie la clé (format: `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX`)

**Important**: Cette clé est **lecture seule** et ne permet pas de modifier ton compte.

## 🚀 Déclenchement du Workflow

### Automatique

Le workflow se déclenche automatiquement sur:
- ✅ Push sur `main`
- ✅ Push sur `dev`

### Manuel

Tu peux aussi lancer le workflow manuellement:
1. Va dans **Actions**
2. Sélectionne **🧪 GW2Optimizer - Real Conditions E2E Test**
3. Clique sur **Run workflow**
4. Choisis la branche
5. Clique sur **Run workflow**

## 📊 Résultats du Test

### Artifacts Générés

Après chaque exécution, 2 artifacts sont disponibles:

1. **gw2optimizer-test-report** (30 jours)
   - `test_report.txt`: Rapport détaillé de tous les tests
   - Summary: Tests passés/échoués

2. **gw2optimizer-logs** (30 jours)
   - `backend.log`: Logs du serveur FastAPI
   - `frontend.log`: Logs du serveur Vite
   - `response.json`: Réponses API Mistral
   - `gw2optimizer_test.db`: Base de données SQLite utilisée

### Télécharger les Artifacts

1. Va dans **Actions**
2. Clique sur le run terminé
3. Scroll vers le bas jusqu'à **Artifacts**
4. Clique sur le nom pour télécharger

## 🧪 Tests Exécutés

### Tests Backend

| Test | Description |
|------|-------------|
| **Health Check** | Vérifie que le backend répond |
| **API Docs** | Vérifie l'accessibilité de `/docs` |
| **Registration** | Crée un utilisateur test |
| **Login** | Authentifie l'utilisateur |
| **Protected Endpoint** | Teste l'autorisation JWT |
| **Build Creation** | Crée un build avec token |

### Tests Externes

| Test | Description | Requis |
|------|-------------|--------|
| **GW2 API** | Vérifie connexion API ArenaNet | `GW2_API_KEY` |
| **Mistral AI** | Génère un build avec IA | `MISTRAL_API_KEY` |

## 🔍 Analyse Auto par Claude

Claude peut analyser automatiquement les résultats via:
1. Lecture du `test_report.txt`
2. Analyse des logs backend/frontend
3. Validation de la réponse Mistral
4. Diagnostic des échecs éventuels

## ⚠️ Troubleshooting

### "Backend health check failed"

**Cause**: Le backend n'a pas démarré à temps

**Solution**:
- Vérifie les logs dans `backend.log`
- Augmente le `sleep` dans le workflow
- Vérifie les dépendances Python

### "Mistral AI integration failed"

**Causes possibles**:
1. Clé API invalide
2. Crédits épuisés
3. Quota dépassé

**Solutions**:
- Vérifie ta clé sur console.mistral.ai
- Vérifie tes crédits restants
- Attends la réinitialisation du quota

### "GW2 API integration failed"

**Causes possibles**:
1. Clé API invalide
2. Permissions insuffisantes
3. Clé expirée

**Solutions**:
- Régénère une clé dans le jeu
- Vérifie les permissions (account, characters, builds)
- Utilise une clé récente

## 📈 Métriques de Success

Pour qu'un run soit considéré comme **réussi**:
- ✅ Tous les tests backend passent (7/7)
- ✅ Au moins 1 test externe passe (GW2 ou Mistral)
- ✅ Aucune exception non gérée
- ✅ Services démarrent en < 30s

## 🔄 Fréquence Recommandée

| Type de Push | Exécution |
|--------------|-----------|
| **main** | Toujours |
| **dev** | Toujours |
| **feature branches** | Manuel uniquement |

## 🛠️ Maintenance

### Mise à jour des dépendances

Si tu ajoutes de nouvelles dépendances:
1. Backend: Mets à jour `requirements.txt`
2. Frontend: Mets à jour `package.json`
3. Le workflow les installera automatiquement

### Ajout de nouveaux tests

Pour ajouter des tests dans `test_real_conditions_extended.sh`:
1. Utilise les fonctions `log_success()` et `log_error()`
2. Incrémente les compteurs automatiquement
3. Ajoute la documentation ici

## 🎯 Next Steps

Après configuration:
1. ✅ Pousse sur `main` ou `dev`
2. ✅ Va dans **Actions** et regarde l'exécution
3. ✅ Télécharge les artifacts si besoin
4. ✅ Claude analysera automatiquement les résultats

---

**Questions?** Ouvre une issue ou contacte le maintainer.
