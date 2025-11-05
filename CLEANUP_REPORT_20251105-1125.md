# Rapport de nettoyage du dépôt ($dateTag)

## Résumé
- Point de restauration : tag `pre-cleanup-$dateTag` et branche `backup/cleanup-$dateTag`
- PRs ouvertes : $open_count
- Branches distantes fusionnées et supprimables : $merged_count

## PRs ouvertes
Les PRs suivantes sont actuellement ouvertes :
- 21: chore: start 4.2.1-dev and add Unreleased
- 19: chore(deps-dev): bump ipython from 8.20.0 to 9.6.0 in /backend
- 18: chore(deps): bump lucide-react from 0.546.0 to 0.552.0 in /frontend
- 17: chore(deps-dev): bump @types/node from 24.9.1 to 24.10.0 in /frontend
- 16: chore(deps-dev): bump mkdocs-material from 9.5.6 to 9.6.23 in /backend
- 15: chore(deps): bump psycopg2-binary from 2.9.9 to 2.9.11 in /backend
- 14: chore(deps-dev): bump globals from 16.4.0 to 16.5.0 in /frontend
- 13: chore(deps): bump sqlalchemy from 2.0.25 to 2.0.44 in /backend
- 12: chore(deps-dev): bump @eslint/js from 9.38.0 to 9.39.0 in /frontend
- 11: chore(deps-dev): bump @vitest/ui from 3.2.4 to 4.0.6 in /frontend
- 10: chore(deps-dev): bump mkdocs from 1.5.3 to 1.6.1 in /backend
- 9: style: apply ruff format (line-length 120) + trivial script fixes

## Branches fusionnées à supprimer
Les branches suivantes sont fusionnées dans main et peuvent être supprimées :
- audit/swe1-20251103
- deps/batch1-ruff-f541-and-audit

## Actions recommandées
1. Supprimer les branches distantes fusionnées :
   ```bash
   git push origin --delete audit/swe1-20251103 deps/batch1-ruff-f541-and-audit
   ```

2. Passer en revue les PRs ouvertes, en particulier :
   - PR #9 (style/ruff-format-120) qui est marquée comme DIRTY
   - Les mises à jour de dépendances (dependabot)

3. Activer l'option "Automatically delete head branches" dans les paramètres du dépôt GitHub (Settings > General > Pull Requests)

## Notes
- Les branches protégées (main, release/*, gh-pages, backup/*) sont conservées
- Aucun conflit n'a été résolu automatiquement
- Les branches non fusionnées avec des PRs ouvertes sont conservées
