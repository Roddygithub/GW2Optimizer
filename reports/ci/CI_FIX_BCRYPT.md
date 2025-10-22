# 🔧 CI Fix - bcrypt Compatibility

**Date**: 2025-10-21 23:46  
**Run**: #30 (18698480045)  
**Status**: ❌ → 🔄 En cours

## Problème Identifié

```
AttributeError: module 'bcrypt' has no attribute '__about__'
```

- **Impact**: 32 tests services en ERROR
- **Cause**: Incompatibilité `passlib[bcrypt]==1.7.4` avec version récente de `bcrypt`

## Solution Appliquée

**Fichier**: `backend/requirements.txt`

```diff
# Authentication
+bcrypt==4.0.1
passlib[bcrypt]==1.7.4
```

## Commit

- **Hash**: `13b7ca0`
- **Message**: `fix(deps): pin bcrypt to 4.0.1 for passlib compatibility`

## Prochain Run CI

- Déclenché automatiquement par le push
- Attendu: ✅ Tous tests passent
- URL: https://github.com/Roddygithub/GW2Optimizer/actions
