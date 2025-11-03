# [P1] Amélioration de la couverture des tests frontend

## Description
La couverture des tests frontend est actuellement à $(jq '.total.lines.pct' audit-reports/coverage/coverage-summary.json 2>/dev/null || echo "X")%, en dessous de l'objectif de 80%.

## Composants à couvrir
```
$(jq '. | to_entries[] | select(.value.lines.pct < 80) | "- " + .key + ": " + (.value.lines.pct | tostring) + "%"' audit-reports/coverage/coverage-summary.json 2>/dev/null || echo "Aucun composant spécifique identifié")
```

## Actions recommandées
1. Identifier les composants critiques non couverts
2. Ajouter des tests unitaires pour ces composants
3. Mettre en place des tests d'intégration pour les flux utilisateur clés
4. Configurer un seuil de couverture minimum dans la CI

## Critères d'acceptation
- [ ] Couverture globale ≥ 80%
- [ ] Tous les composants critiques ont une couverture ≥ 90%
- [ ] Nouveaux tests ajoutés pour les cas limites
