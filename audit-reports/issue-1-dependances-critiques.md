# [P0] Mise à jour des dépendances critiques

## Description
Plusieurs dépendances présentent des vulnérabilités critiques qui doivent être mises à jour de toute urgence.

## Vulnérabilités identifiées
### Backend (pip-audit)
```json
$(jq -r '.vulnerabilities[] | "- " + .name + " " + .installed_version + " → " + .fix_versions[]' audit-reports/pip-audit.json 2>/dev/null || echo "Aucune vulnérabilité critique identifiée")
```

### Frontend (npm audit)
```json
$(jq -r '.vulnerabilities[] | select(.severity == "critical" or .severity == "high") | "- " + .name + " " + .range + " (" + .severity + ")"' audit-reports/npm-audit.json 2>/dev/null || echo "Aucune vulnérabilité critique identifiée")
```

## Actions recommandées
1. Mettre à jour les dépendances listées ci-dessus vers les versions sécurisées
2. Exécuter les tests complets après chaque mise à jour
3. Vérifier la rétrocompatibilité

## Critères d'acceptation
- [ ] Toutes les dépendances critiques mises à jour
- [ ] Tous les tests passent avec succès
- [ ] Aucune régression fonctionnelle détectée
