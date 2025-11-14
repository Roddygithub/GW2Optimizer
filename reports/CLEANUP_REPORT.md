🧹 Cleanup Report – v0.4.0-clean (2025-11-14)

Backend

Vulture (dead code): 304 lignes
Principalement des “unused variables” dans les migrations Alembic (révision, down_revision, etc.) → faux positifs attendus

Radon (complexity): 532 fonctions ≥ C
Top extrait (grade A montrés dans l’échantillon), aucun hot spot critique identifié dans cet audit

Radon (maintainability): 0 fichiers < C (bon)

Deptry (unused deps): 0 packages

Bandit (security): 1384 issues scan, HIGH=0, MEDIUM=0
B101 (assert_used) signalé dans plusieurs fichiers (faible sévérité, souvent test-only)

Décision backend:
Pas d’autoflake massif (risque de faux positifs dans main.py, core/security.py, endpoints)
Aucun hotspot sécurité/maintenabilité bloquant

Frontend

ts-prune (dead exports): 0

depcheck (unused deps):
dependencies: 0
devDependencies (7 suspects, probablement utilisés via scripts/config): tailwindcss, postcss, @testing-library/user-event, @types/jest, @vitest/coverage-v8, autoprefixer, wait-on

Build & bundle:
Total: 684 KB
Plus gros chunk: 444 KB (pré-gzip ~137.7 KB gz)
Top assets:
dist/assets/index-…js 443.91 kB (gzip: 137.68 kB)
dist/assets/ui-…js 120.14 kB (gzip: 38.95 kB)
dist/assets/vendor-…js 62.43 kB (gzip: 21.77 kB)
dist/assets/react-…js 43.07 kB (gzip: 15.22 kB)
dist/assets/index-…css 9.13 kB (gzip: 2.44 kB)

Recommandations frontend:
Code-splitting ciblé (React.lazy + Suspense) pour routes/pages volumineuses (auth/builds/teams)
Vérifier le bundle “ui-*.js” (~120 KB) pour d’éventuels re-exports inutiles
Conserver vendor split actuel
Revue manuelle des 7 devDeps flaggées par depcheck (scripts/config)

Décisions & actions
Backend: SKIP autoflake massif (code sain, risques supérieurs aux gains)
Frontend: Actions de suivi proposées (voir issues ci-dessous)

Prochaines étapes (issues)
Frontend bundle: candidates de code-splitting
Depcheck: revue devDependencies flaggées (7)
