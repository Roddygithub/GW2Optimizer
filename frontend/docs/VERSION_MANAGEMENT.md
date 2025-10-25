# 📦 Gestion de Version - GW2 Optimizer

Ce document explique comment gérer et afficher la version de l'application GW2 Optimizer.

## 🎯 Vue d'ensemble

Le système de gestion de version offre **3 méthodes** pour accéder aux informations de version :

1. **Terminal** : `npm run version`
2. **Console navigateur** : `window.showAppVersion()`
3. **Interface React** : Hook `useAppVersion()`

---

## 📁 Architecture

```
frontend/
├── package.json                    # Version NPM principale
├── scripts/
│   └── show-version.js            # Script CLI Node.js
├── src/
│   ├── config/
│   │   └── version.ts             # Configuration centralisée
│   ├── hooks/
│   │   └── useAppVersion.ts       # Hook React + utilitaires
│   ├── components/
│   │   └── ui/
│   │       └── VersionDisplay.tsx # Composant d'affichage
│   └── main.tsx                   # Point d'entrée (expose window.showAppVersion)
```

---

## 🚀 Utilisation

### 1️⃣ Depuis le Terminal

```bash
# Affiche toutes les informations de version
npm run version
```

**Sortie attendue :**
```
============================================================
🎮 GW2 Optimizer - Informations de Version
============================================================

📦 Package Version:     v4.1.0
⚙️  Config Version:      v4.1.0
📛 Application Name:    GW2 Optimizer
📝 Subtitle:            WvW McM Dashboard
🔧 Node Version:        v20.x.x
📅 Build Date:          24 octobre 2025, 14:37

============================================================
✅ Toutes les versions sont synchronisées !
```

---

### 2️⃣ Depuis la Console du Navigateur

Ouvrez les DevTools (F12) et tapez :

```javascript
// Affiche les informations complètes
window.showAppVersion()

// Récupère les informations en tant qu'objet
window.getAppVersion()
```

**Sortie console :**
```
============================================================
🎮 GW2 Optimizer - Informations de Version
============================================================
📦 Version: 4.1.0
📛 Application: GW2 Optimizer
📝 Subtitle: WvW McM Dashboard
📅 Build Date: 24/10/2025 14:37:00
©️ Copyright: © 2025 - WvW McM Dashboard
============================================================
💡 Astuce: Tapez window.showAppVersion() pour réafficher ces informations
```

---

### 3️⃣ Depuis un Composant React

#### Utilisation du Hook

```tsx
import { useAppVersion } from '../hooks/useAppVersion';

function MyComponent() {
  const { version, name, subtitle, showVersion } = useAppVersion();

  return (
    <div>
      <p>{name} v{version}</p>
      <p>{subtitle}</p>
      <button onClick={showVersion}>
        Afficher les détails
      </button>
    </div>
  );
}
```

#### Utilisation du Composant VersionDisplay

```tsx
import { VersionDisplay } from '../components/ui/VersionDisplay';

// Affichage minimal
<VersionDisplay variant="minimal" />

// Affichage inline avec bouton
<VersionDisplay variant="inline" showButton={true} />

// Affichage en carte
<VersionDisplay variant="card" showButton={true} />
```

---

## 🔧 Mise à Jour de la Version

Pour mettre à jour la version de l'application :

### 1. Modifier la version dans `package.json`

```json
{
  "version": "4.2.0"
}
```

### 2. Modifier la version dans `src/config/version.ts`

```typescript
export const APP_VERSION = '4.2.0';
```

### 3. Vérifier la synchronisation

```bash
npm run version
```

Si les versions ne correspondent pas, vous verrez un avertissement :

```
⚠️  ATTENTION: Les versions ne correspondent pas !
   package.json: v4.2.0
   version.ts:   v4.1.0
   
   Pensez à synchroniser les versions.
```

### 4. Mettre à jour le CHANGELOG

Ajoutez une entrée dans `CHANGELOG.md` :

```markdown
## [4.2.0] - 2025-10-XX

### ✨ Ajouté
- Nouvelle fonctionnalité X

### 🔄 Modifié
- Amélioration Y
```

---

## 📊 API du Hook useAppVersion

### Interface AppVersionInfo

```typescript
interface AppVersionInfo {
  version: string;        // "4.1.0"
  name: string;          // "GW2 Optimizer"
  subtitle: string;      // "WvW McM Dashboard"
  fullTitle: string;     // "GW2 Optimizer v4.1.0 - WvW McM Dashboard"
  copyright: string;     // "© 2025 - WvW McM Dashboard"
  buildDate: string;     // ISO 8601 date
}
```

### Fonctions Exportées

#### `useAppVersion(options?)`

Hook React principal.

```typescript
const { 
  version, 
  name, 
  subtitle, 
  fullTitle, 
  copyright, 
  buildDate, 
  showVersion 
} = useAppVersion({ logOnMount: true });
```

**Options :**
- `logOnMount?: boolean` - Affiche la version dans la console au montage du composant

#### `showAppVersion()`

Affiche les informations de version dans la console.

```typescript
import { showAppVersion } from '../hooks/useAppVersion';

showAppVersion(); // Affiche dans la console
```

#### `getAppVersion()`

Retourne les informations de version en tant qu'objet.

```typescript
import { getAppVersion } from '../hooks/useAppVersion';

const versionInfo = getAppVersion();
console.log(versionInfo.version); // "4.1.0"
```

#### `exposeVersionToWindow()`

Expose les fonctions dans `window` (déjà appelé dans `main.tsx`).

```typescript
import { exposeVersionToWindow } from '../hooks/useAppVersion';

exposeVersionToWindow();
// Maintenant disponible : window.showAppVersion()
```

---

## 🎨 Exemples d'Intégration

### Dans la Sidebar

```tsx
import { VersionDisplay } from '../components/ui/VersionDisplay';

<div className="sidebar-footer">
  <VersionDisplay variant="card" showButton={true} />
</div>
```

### Dans les Paramètres

```tsx
import { useAppVersion } from '../hooks/useAppVersion';

function SettingsPage() {
  const { version, name, buildDate } = useAppVersion();

  return (
    <div>
      <h2>À propos</h2>
      <dl>
        <dt>Application</dt>
        <dd>{name}</dd>
        
        <dt>Version</dt>
        <dd>{version}</dd>
        
        <dt>Date de build</dt>
        <dd>{new Date(buildDate).toLocaleDateString('fr-FR')}</dd>
      </dl>
    </div>
  );
}
```

### Dans le Footer

```tsx
import { VersionDisplay } from '../components/ui/VersionDisplay';

<footer>
  <VersionDisplay variant="minimal" showButton={false} />
</footer>
```

---

## 🧪 Tests

### Tester le script CLI

```bash
npm run version
```

### Tester dans le navigateur

1. Lancez l'application : `npm run dev`
2. Ouvrez la console (F12)
3. Vérifiez le message de bienvenue : `🚀 GW2 Optimizer v4.1.0`
4. Tapez : `window.showAppVersion()`

### Tester dans un composant

Créez un composant de test :

```tsx
import { useAppVersion } from '../hooks/useAppVersion';

export function VersionTest() {
  const versionInfo = useAppVersion({ logOnMount: true });
  
  return (
    <div>
      <pre>{JSON.stringify(versionInfo, null, 2)}</pre>
    </div>
  );
}
```

---

## 🔒 Bonnes Pratiques

1. **Toujours synchroniser** `package.json` et `version.ts`
2. **Utiliser Semantic Versioning** : MAJOR.MINOR.PATCH
3. **Documenter les changements** dans `CHANGELOG.md`
4. **Tester après chaque mise à jour** avec `npm run version`
5. **Ne jamais coder en dur** la version dans les composants

---

## 🐛 Dépannage

### Les versions ne correspondent pas

```bash
npm run version
```

Vérifiez et synchronisez :
- `package.json` → `"version": "X.Y.Z"`
- `src/config/version.ts` → `APP_VERSION = 'X.Y.Z'`

### window.showAppVersion() n'est pas défini

Vérifiez que `exposeVersionToWindow()` est appelé dans `main.tsx`.

### La version ne s'affiche pas dans la console

Vérifiez que le navigateur n'a pas désactivé les logs console.

---

## 📚 Ressources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [React Hooks Documentation](https://react.dev/reference/react)

---

**Dernière mise à jour :** 24 octobre 2025
