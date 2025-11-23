# GW2Optimizer Frontend

Frontend de l'application **GW2Optimizer** (SPA React/TypeScript).
Pour la vue d'ensemble de la plateforme et de la stack globale, voir également le README à la racine du dépôt.

## Tech Stack

- **Framework** : React 19 + TypeScript + Vite
- **State Management** : Zustand
- **HTTP Client** : Axios
- **UI** : TailwindCSS (avec `tailwind-merge`, `tailwindcss-animate`, `lucide-react`)
- **Tests** : Vitest, Testing Library, Playwright

## Scripts principaux

Depuis la racine du dépôt :

```bash
# Installation des dépendances
npm --prefix frontend install

# Démarrer le serveur de dev
npm --prefix frontend run dev

# Lancer les tests unitaires
npm --prefix frontend test

# Lancer les tests end-to-end (Playwright)
npm --prefix frontend run test:e2e
```
