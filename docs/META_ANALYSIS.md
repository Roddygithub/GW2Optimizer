# Meta Analysis System - Documentation

## 📋 Vue d'ensemble

Le système d'analyse de méta (v1.1.0) permet d'analyser automatiquement les tendances du méta Guild Wars 2, de scorer la viabilité des builds, et de générer des recommandations d'adaptation.

---

## 🎯 Composants

### 1. MetaAgent

Agent IA spécialisé dans l'analyse et l'adaptation de méta.

**Capacités**:
- Analyse des tendances de builds populaires
- Détection automatique des changements de méta
- Scoring de viabilité des builds (0.0 - 1.0)
- Recommandations d'adaptation par priorité
- Prédictions d'évolution du méta

**Modes de jeu supportés**:
- `zerg`: Grandes armées (25+ joueurs)
- `raid_guild`: Groupes organisés (15-25 joueurs)
- `roaming`: Petits groupes (1-5 joueurs)

### 2. GW2APIClient

Client pour l'API officielle Guild Wars 2.

**Fonctionnalités**:
- Importation automatique des professions
- Récupération des spécialisations
- Import des traits et compétences
- Système de cache avec TTL (24h)
- Retry automatique (3 tentatives)
- Support des requêtes paginées (200 items/page)

**Endpoints API supportés**:
- `/v2/professions`: Professions et mécaniques
- `/v2/skills`: Compétences
- `/v2/traits`: Traits
- `/v2/specializations`: Spécialisations
- `/v2/items`: Items et équipement
- `/v2/itemstats`: Statistiques d'items

### 3. MetaAnalysisWorkflow

Workflow orchestrant l'analyse complète du méta.

**Étapes**:
1. **Collecte des données** (optionnel): Import depuis l'API GW2
2. **Analyse du méta**: État actuel du méta
3. **Détection des tendances**: Identification des changements
4. **Génération de recommandations**: Actions suggérées
5. **Création du rapport**: Rapport détaillé avec insights

---

## 🚀 Utilisation

### Analyse de méta basique

```python
from app.workflows.meta_analysis_workflow import MetaAnalysisWorkflow

workflow = MetaAnalysisWorkflow()
await workflow.initialize()

result = await workflow.run({
    "game_mode": "zerg",
    "time_range": 30
})

print(result["report"]["executive_summary"])
```

### Analyse avec profession spécifique

```python
result = await workflow.run({
    "game_mode": "raid_guild",
    "profession": "Guardian",
    "time_range": 14
})
```

### Analyse avec import de données API

```python
result = await workflow.run({
    "game_mode": "zerg",
    "profession": "Guardian",
    "include_api_data": True,
    "time_range": 30
})
```

### Analyse de builds existants

```python
builds = [
    {
        "id": "build_1",
        "role": "support",
        "profession": "Guardian"
    },
    {
        "id": "build_2",
        "role": "dps",
        "profession": "Warrior"
    }
]

result = await workflow.run({
    "game_mode": "zerg",
    "current_builds": builds,
    "time_range": 30
})

viability_scores = result["report"]["viability_scores"]
```

---

## 📡 API Endpoints

### POST /api/v1/meta/analyze

Analyse complète du méta.

**Request**:
```json
{
  "game_mode": "zerg",
  "profession": "Guardian",
  "include_api_data": true,
  "time_range": 30
}
```

**Response**:
```json
{
  "success": true,
  "report": {
    "title": "Meta Analysis Report",
    "game_mode": "zerg",
    "profession": "Guardian",
    "analysis_period": "30 days",
    "executive_summary": {
      "total_trends_detected": 3,
      "strong_trends": 1,
      "average_build_viability": 0.72,
      "total_recommendations": 5,
      "high_priority_recommendations": 2,
      "meta_stability": "shifting",
      "key_insights": [
        "Tendance principale: Augmentation des builds support",
        "2 builds nécessitent une optimisation",
        "2 actions prioritaires recommandées"
      ]
    },
    "meta_snapshot": { ... },
    "trends": [ ... ],
    "recommendations": [ ... ],
    "viability_scores": { ... },
    "predictions": { ... }
  }
}
```

### GET /api/v1/meta/snapshot/{game_mode}

Snapshot rapide du méta (7 jours).

**Request**:
```
GET /api/v1/meta/snapshot/zerg?profession=Guardian
```

**Response**:
```json
{
  "success": true,
  "snapshot": {
    "game_mode": "zerg",
    "profession": "Guardian",
    "top_builds": [],
    "popular_roles": [
      {"role": "support", "popularity": 0.35},
      {"role": "dps", "popularity": 0.40}
    ],
    "common_synergies": []
  },
  "trends": [ ... ]
}
```

### POST /api/v1/meta/import-gw2-data

Import des données depuis l'API GW2.

**Request**:
```json
{
  "data_types": ["professions", "specializations", "traits"],
  "profession": "Guardian"
}
```

**Response**:
```json
{
  "success": true,
  "stats": {
    "professions_imported": 0,
    "profession_imported": true,
    "specializations_imported": 7,
    "traits_imported": 150
  },
  "data": { ... }
}
```

### GET /api/v1/meta/gw2-api/professions

Liste des professions GW2.

**Response**:
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

### GET /api/v1/meta/gw2-api/profession/{profession_id}

Détails d'une profession.

**Response**:
```json
{
  "success": true,
  "profession": {
    "id": "Guardian",
    "name": "Guardian",
    "code": 1,
    "icon": "https://...",
    "specializations": [13, 16, 27, 42, 46, 62, 65]
  }
}
```

### GET /api/v1/meta/cache/stats

Statistiques du cache API.

**Response**:
```json
{
  "success": true,
  "cache_stats": {
    "cache_size": 42,
    "cache_ttl_hours": 24
  }
}
```

### POST /api/v1/meta/cache/clear

Vide le cache API.

**Response**:
```json
{
  "success": true,
  "message": "Cache cleared successfully"
}
```

---

## 📊 Structure du rapport

### Executive Summary

```json
{
  "total_trends_detected": 3,
  "strong_trends": 1,
  "average_build_viability": 0.72,
  "total_recommendations": 5,
  "high_priority_recommendations": 2,
  "meta_stability": "shifting",
  "key_insights": [
    "Tendance principale: ...",
    "X builds nécessitent une optimisation",
    "Y actions prioritaires recommandées"
  ]
}
```

### Meta Snapshot

```json
{
  "game_mode": "zerg",
  "profession": "Guardian",
  "top_builds": [],
  "popular_roles": [
    {"role": "support", "popularity": 0.35},
    {"role": "dps", "popularity": 0.40},
    {"role": "tank", "popularity": 0.15},
    {"role": "healer", "popularity": 0.10}
  ],
  "common_synergies": [],
  "timestamp": "2025-10-20T20:00:00Z"
}
```

### Trends

```json
[
  {
    "type": "build_popularity",
    "description": "Augmentation de la popularité des builds support",
    "change_percentage": 0.18,
    "confidence": 0.85,
    "detected_at": "2025-10-20T20:00:00Z"
  }
]
```

### Recommendations

```json
[
  {
    "type": "trend_adaptation",
    "priority": "high",
    "description": "Adapter aux tendances: ...",
    "suggested_actions": [
      "Considérer les builds support",
      "Renforcer les synergies d'équipe"
    ],
    "confidence": 0.85
  },
  {
    "type": "viability_improvement",
    "priority": "medium",
    "description": "2 builds avec faible viabilité détectés",
    "suggested_actions": [
      "Revoir les rôles des builds",
      "Optimiser les synergies",
      "Mettre à jour l'équipement"
    ],
    "affected_builds": ["build_1", "build_3"]
  }
]
```

### Viability Scores

```json
{
  "build_1": 0.45,
  "build_2": 0.82,
  "build_3": 0.38,
  "build_4": 0.91
}
```

**Interprétation**:
- `0.0 - 0.3`: Viabilité très faible
- `0.3 - 0.5`: Viabilité faible
- `0.5 - 0.7`: Viabilité moyenne
- `0.7 - 0.9`: Bonne viabilité
- `0.9 - 1.0`: Excellente viabilité

### Predictions

```json
{
  "timeframe": "30 days",
  "confidence": 0.65,
  "expected_changes": [
    {
      "type": "role_shift",
      "description": "Augmentation probable des builds support",
      "probability": 0.75
    }
  ],
  "risk_factors": [
    {
      "type": "game_balance_patch",
      "description": "Patch d'équilibrage pourrait modifier le méta",
      "impact": "high"
    }
  ]
}
```

---

## 🎯 Niveaux de stabilité du méta

### Stable
- Peu ou pas de tendances fortes
- Changements < 15%
- Méta établi et prévisible

### Shifting
- 1-2 tendances significatives
- Changements 15-25%
- Méta en évolution

### Volatile
- 3+ tendances significatives
- Changements > 25%
- Méta instable et imprévisible

---

## 🔧 Configuration

### Variables d'environnement

Aucune configuration spécifique requise. Le système utilise les paramètres par défaut:

- **Cache TTL**: 24 heures
- **Trend Threshold**: 15%
- **Max Retries**: 3
- **Request Timeout**: 30 secondes

### Personnalisation

```python
from app.agents.meta_agent import MetaAgent

agent = MetaAgent()
agent.trend_threshold = 0.20  # 20% au lieu de 15%
```

```python
from app.services.gw2_api_client import GW2APIClient

client = GW2APIClient(
    api_key="your-api-key",
    timeout=60,
    max_retries=5
)
```

---

## 🧪 Tests

### Exécuter les tests

```bash
# Tous les tests Meta
pytest backend/tests/test_meta_agent.py -v
pytest backend/tests/test_gw2_api_client.py -v
pytest backend/tests/test_meta_analysis_workflow.py -v

# Tests spécifiques
pytest backend/tests/test_meta_agent.py::TestMetaAgent::test_meta_agent_viability_scoring -v

# Avec couverture
pytest backend/tests/test_meta_*.py --cov=app.agents.meta_agent --cov=app.services.gw2_api_client --cov=app.workflows.meta_analysis_workflow
```

### Coverage attendue

- **MetaAgent**: 90%+
- **GW2APIClient**: 85%+
- **MetaAnalysisWorkflow**: 90%+

---

## 📚 Exemples avancés

### Analyse multi-professions

```python
professions = ["Guardian", "Warrior", "Necromancer"]

for profession in professions:
    result = await workflow.run({
        "game_mode": "zerg",
        "profession": profession,
        "time_range": 30
    })
    
    print(f"{profession}: {result['report']['executive_summary']}")
```

### Comparaison de périodes

```python
# Analyse court terme (7 jours)
result_7d = await workflow.run({
    "game_mode": "zerg",
    "time_range": 7
})

# Analyse long terme (90 jours)
result_90d = await workflow.run({
    "game_mode": "zerg",
    "time_range": 90
})

# Comparer les tendances
trends_7d = result_7d["report"]["trends"]
trends_90d = result_90d["report"]["trends"]
```

### Monitoring continu

```python
import asyncio

async def monitor_meta():
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
            # Envoyer une notification
        
        await asyncio.sleep(3600)  # Vérifier toutes les heures

asyncio.run(monitor_meta())
```

---

## 🐛 Troubleshooting

### Erreur: "Failed to fetch professions"

**Cause**: L'API GW2 est inaccessible ou rate-limitée.

**Solution**:
```python
# Augmenter le timeout et les retries
client = GW2APIClient(timeout=60, max_retries=5)
```

### Erreur: "Invalid game_mode"

**Cause**: Mode de jeu non supporté.

**Solution**: Utiliser `zerg`, `raid_guild`, ou `roaming`.

### Cache trop volumineux

**Solution**:
```python
# Vider le cache régulièrement
client = GW2APIClient()
client.clear_cache()
```

---

## 🔮 Roadmap v1.2.0

- [ ] Intégration avec la base de données pour historique
- [ ] Machine Learning pour prédictions améliorées
- [ ] Support des builds communautaires (Snowcrows, MetaBattle)
- [ ] Notifications temps réel des changements de méta
- [ ] Dashboard de visualisation des tendances
- [ ] Export des rapports en PDF/HTML

---

## 📞 Support

Pour toute question ou problème:
1. Consulter cette documentation
2. Vérifier les logs: `backend/logs/gw2optimizer.log`
3. Exécuter les tests: `pytest backend/tests/test_meta_*.py -v`
4. Créer une issue sur GitHub

---

**Version**: 1.1.0  
**Dernière mise à jour**: 2025-10-20  
**Auteur**: Roddy
