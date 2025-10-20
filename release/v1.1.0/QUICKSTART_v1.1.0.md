# 🚀 Quick Start - GW2Optimizer v1.1.0

Guide de démarrage rapide pour les nouvelles fonctionnalités Meta Analysis.

---

## ⚡ Installation rapide

```bash
# 1. Cloner le projet (si pas déjà fait)
git clone https://github.com/USERNAME/GW2Optimizer.git
cd GW2Optimizer

# 2. Installer les dépendances backend
cd backend
pip install -r requirements.txt

# 3. Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur démarre sur **http://localhost:8000**

---

## 🧪 Tester les nouvelles fonctionnalités

### 1. Vérifier que l'API fonctionne

```bash
# Health check
curl http://localhost:8000/health

# Liste des professions GW2
curl http://localhost:8000/api/v1/meta/gw2-api/professions
```

**Réponse attendue**:
```json
{
  "success": true,
  "professions": [
    "Guardian", "Warrior", "Engineer", "Ranger",
    "Thief", "Elementalist", "Mesmer", "Necromancer", "Revenant"
  ],
  "count": 9
}
```

### 2. Obtenir un snapshot du méta

```bash
curl "http://localhost:8000/api/v1/meta/snapshot/zerg"
```

**Réponse**:
```json
{
  "success": true,
  "snapshot": {
    "game_mode": "zerg",
    "popular_roles": [
      {"role": "support", "popularity": 0.35},
      {"role": "dps", "popularity": 0.40},
      {"role": "tank", "popularity": 0.15},
      {"role": "healer", "popularity": 0.10}
    ]
  },
  "trends": [...]
}
```

### 3. Analyser le méta complet

```bash
curl -X POST http://localhost:8000/api/v1/meta/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "game_mode": "zerg",
    "profession": "Guardian",
    "time_range": 30
  }'
```

**Réponse**: Rapport d'analyse complet avec:
- Executive summary
- Meta snapshot
- Tendances détectées
- Recommandations
- Scores de viabilité
- Prédictions

### 4. Importer des données GW2

```bash
curl -X POST http://localhost:8000/api/v1/meta/import-gw2-data \
  -H "Content-Type: application/json" \
  -d '{
    "data_types": ["professions", "specializations"],
    "profession": "Guardian"
  }'
```

---

## 🧪 Exécuter les tests

```bash
cd backend

# Tous les tests v1.1.0
pytest tests/test_meta_*.py -v

# Tests spécifiques
pytest tests/test_meta_agent.py -v
pytest tests/test_gw2_api_client.py -v
pytest tests/test_meta_analysis_workflow.py -v

# Avec couverture
pytest tests/test_meta_*.py --cov=app --cov-report=html
```

**Résultat attendu**: 45 tests passent ✅

---

## 📖 Utilisation en Python

### Exemple 1: Utiliser le Meta Agent

```python
from app.agents.meta_agent import MetaAgent

# Créer l'agent
agent = MetaAgent()
await agent.initialize()

# Analyser le méta
result = await agent.run({
    "game_mode": "zerg",
    "profession": "Guardian",
    "time_range": 30
})

# Afficher les résultats
print(f"Tendances: {result['trends']}")
print(f"Recommandations: {result['recommendations']}")
print(f"Scores: {result['viability_scores']}")
```

### Exemple 2: Utiliser le client API GW2

```python
from app.services.gw2_api_client import GW2APIClient

# Créer le client
client = GW2APIClient()

# Récupérer les professions
professions = await client.get_professions()
print(f"Professions: {professions}")

# Récupérer les détails d'une profession
guardian = await client.get_profession("Guardian")
print(f"Guardian specs: {guardian['specializations']}")

# Importer toutes les données
data = await client.import_all_game_data()
print(f"Imported: {len(data['professions'])} professions")
```

### Exemple 3: Utiliser le workflow complet

```python
from app.workflows.meta_analysis_workflow import MetaAnalysisWorkflow

# Créer le workflow
workflow = MetaAnalysisWorkflow()
await workflow.initialize()

# Exécuter l'analyse complète
result = await workflow.run({
    "game_mode": "raid_guild",
    "profession": "Guardian",
    "include_api_data": True,
    "time_range": 30
})

# Afficher le rapport
report = result["report"]
print(f"Stabilité: {report['executive_summary']['meta_stability']}")
print(f"Insights: {report['executive_summary']['key_insights']}")
```

---

## 🎯 Cas d'usage typiques

### Cas 1: Analyser le méta actuel pour un mode de jeu

**Objectif**: Comprendre l'état actuel du méta zerg

```bash
curl -X POST http://localhost:8000/api/v1/meta/analyze \
  -H "Content-Type: application/json" \
  -d '{"game_mode": "zerg", "time_range": 7}'
```

### Cas 2: Vérifier la viabilité de mes builds

**Objectif**: Scorer mes builds actuels

```python
builds = [
    {"id": "my_guardian", "role": "support", "profession": "Guardian"},
    {"id": "my_warrior", "role": "dps", "profession": "Warrior"}
]

result = await workflow.run({
    "game_mode": "zerg",
    "current_builds": builds,
    "time_range": 30
})

scores = result["report"]["viability_scores"]
# my_guardian: 0.85 (bonne viabilité)
# my_warrior: 0.45 (faible viabilité)
```

### Cas 3: Importer les données d'une profession

**Objectif**: Obtenir toutes les données Guardian

```bash
curl -X POST http://localhost:8000/api/v1/meta/import-gw2-data \
  -H "Content-Type: application/json" \
  -d '{
    "data_types": ["professions", "specializations", "traits"],
    "profession": "Guardian"
  }'
```

### Cas 4: Monitoring du méta

**Objectif**: Surveiller les changements de méta

```python
import asyncio

async def monitor():
    workflow = MetaAnalysisWorkflow()
    await workflow.initialize()
    
    while True:
        result = await workflow.run({
            "game_mode": "zerg",
            "time_range": 7
        })
        
        stability = result["report"]["executive_summary"]["meta_stability"]
        
        if stability == "volatile":
            print("⚠️ Méta volatile détecté!")
            # Envoyer notification
        
        await asyncio.sleep(3600)  # Vérifier toutes les heures

asyncio.run(monitor())
```

---

## 📊 Interpréter les résultats

### Scores de viabilité

- **0.0 - 0.3**: ❌ Viabilité très faible - Build non recommandé
- **0.3 - 0.5**: ⚠️ Viabilité faible - Nécessite optimisation
- **0.5 - 0.7**: ✅ Viabilité moyenne - Acceptable
- **0.7 - 0.9**: ✅✅ Bonne viabilité - Recommandé
- **0.9 - 1.0**: 🌟 Excellente viabilité - Optimal

### Stabilité du méta

- **Stable**: 🟢 Méta établi, peu de changements
- **Shifting**: 🟡 Méta en évolution, 1-2 tendances
- **Volatile**: 🔴 Méta instable, 3+ tendances fortes

### Priorités des recommandations

- **High**: 🔴 Action urgente recommandée
- **Medium**: 🟡 Action conseillée
- **Low**: 🟢 Suggestion optionnelle

---

## 🔧 Configuration avancée

### Personnaliser le seuil de détection

```python
agent = MetaAgent()
agent.trend_threshold = 0.20  # 20% au lieu de 15%
```

### Augmenter le timeout API

```python
client = GW2APIClient(timeout=60, max_retries=5)
```

### Utiliser une clé API GW2

```python
client = GW2APIClient(api_key="your-api-key-here")
```

---

## 🐛 Troubleshooting

### Erreur: "Failed to fetch professions"

**Solution**: L'API GW2 est temporairement indisponible. Réessayer plus tard ou augmenter les retries:

```python
client = GW2APIClient(max_retries=5)
```

### Erreur: "Invalid game_mode"

**Solution**: Utiliser uniquement `zerg`, `raid_guild`, ou `roaming`.

### Cache trop volumineux

**Solution**: Vider le cache régulièrement:

```bash
curl -X POST http://localhost:8000/api/v1/meta/cache/clear
```

---

## 📚 Documentation complète

Pour plus de détails, consulter:

- **META_ANALYSIS.md**: Documentation complète du système
- **CHANGELOG.md**: Détails de la version 1.1.0
- **RELEASE_v1.1.0_SUMMARY.md**: Résumé de la release

---

## 🎉 Prochaines étapes

1. ✅ Tester les endpoints API
2. ✅ Exécuter les tests unitaires
3. ✅ Lire la documentation complète
4. ✅ Intégrer dans votre workflow

**Bon développement avec GW2Optimizer v1.1.0! 🚀**

---

**Version**: 1.1.0  
**Date**: 2025-10-20  
**Support**: Consulter docs/META_ANALYSIS.md
