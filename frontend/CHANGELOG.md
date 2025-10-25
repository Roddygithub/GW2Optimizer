# Changelog - GW2 Optimizer Frontend

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [4.1.0] - 2025-10-24

### ✨ Ajouté
- **Système de version centralisé** : Nouveau fichier `/src/config/version.ts` pour gérer toutes les informations de version de manière centralisée
- **Configuration de version dynamique** : Les composants utilisent maintenant des imports pour afficher la version plutôt que des valeurs codées en dur

### 🔄 Modifié
- **package.json** : Version mise à jour de 0.0.0 à 4.1.0
- **package-lock.json** : Version mise à jour dans toutes les occurrences
- **index.html** : Titre de la page mis à jour avec "GW2 Optimizer v4.1.0 - WvW McM Dashboard"
- **Home.tsx** : Utilise maintenant `APP_FULL_TITLE` et `APP_COPYRIGHT` depuis la configuration centralisée
- **Sidebar.tsx** : Utilise maintenant `APP_NAME`, `APP_VERSION` et `APP_COPYRIGHT` depuis la configuration centralisée

### 🎯 Améliorations Techniques
- Centralisation de la gestion de version pour faciliter les mises à jour futures
- Meilleure maintenabilité du code avec une source unique de vérité pour les informations de version
- Cohérence garantie de l'affichage de la version dans toute l'application

### 📝 Fichiers Modifiés
```
frontend/
├── package.json
├── package-lock.json
├── index.html
├── CHANGELOG.md (nouveau)
├── src/
│   ├── config/
│   │   └── version.ts (nouveau)
│   ├── pages/
│   │   └── Home.tsx
│   └── components/
│       └── layout/
│           └── Sidebar.tsx
```

### 🔧 Migration depuis v1.7.0
- Suppression de toutes les références codées en dur à la version 1.7.0
- Remplacement par la version 4.1.0 dans toute l'application
- Introduction d'un système de configuration pour éviter les versions en dur à l'avenir

---

## [1.7.0] - Antérieur

Version legacy avec versions codées en dur.

---

**Note** : Pour mettre à jour la version de l'application à l'avenir, il suffit de modifier le fichier `/src/config/version.ts`.
