# MyPy Progressive Typing Roadmap

## ✅ Phase 1: Auth module (COMPLÉTÉ)

Status: 0 erreurs
Fichiers: `app/api/auth.py`, `app/services/auth_service.py`, `app/main.py`, `app/core/security.py`, `app/core/config.py`
Date: 2025-11-13

---

## 🔄 Phase 2: Core modules (PROCHAIN)

Cible: `app/core/*`, `app/db/*`, `app/models/*`
Erreurs estimées: ~50
Durée estimée: 2h
Priorité: HAUTE (utilisé par auth)

Actions:

```bash
# Diagnostic
poetry run mypy app/core/ app/db/ app/models/ --show-error-codes

# Corrections fichier par fichier
poetry run mypy app/core/config.py
poetry run mypy app/db/session.py
# etc.
```

---

## ⏳ Phase 3: AI services (FUTUR)

Cible: app/ai/*
Erreurs estimées: ~100
Durée estimée: 4h
Priorité: MOYENNE

Défis attendus:
- Types LangChain/OpenAI non stricts
- Callbacks dynamiques
- Dictionnaires non typés

---

## ⏳ Phase 4: Agents (FUTUR)

Cible: app/agents/*
Erreurs estimées: ~150
Durée estimée: 6h
Priorité: BASSE (code expérimental)

---

## 📊 Métriques de progression

| Phase | Fichiers | Erreurs | Status | Date |
|------|----------|---------|--------|------|
| Auth | 5        | 0       | ✅      | 2025-11-13 |
| Core | ~10      | ~50     | ⏳      | - |
| AI   | ~15      | ~100    | ⏳      | - |
| Agents | ~20    | ~150    | ⏳      | - |

Commande pour tracker:

```bash
poetry run mypy app/ --config-file=pyproject.toml | grep "Found" | tee reports/mypy-progress.txt
```

---

## 🎯 Objectif final

Target: `strict = true` sur TOUT `app/` (0 erreurs)
Date visée: Q2 2026

Bénéfices:
- Détection précoce des bugs
- Refactoring sûr
- Documentation implicite via types

---

## ⚙️ Configuration (rappel)

- Modules critiques en mode strict (voir `pyproject.toml`)
- Modules non-critiques temporairement `ignore_errors = true`
- CI utilise `poetry run mypy app/ --config-file=pyproject.toml`

TODO: Retirer `ignore_errors` progressivement par dossier (Core → AI → Agents) en gardant la CI verte.
