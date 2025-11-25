# ⚡ QUICKSTART - GW2 Optimizer Team Commander

> **Commencez en 30 secondes !**

---

## 🚀 Démarrage Ultra-Rapide

```bash
cd /home/roddy/GW2Optimizer

# Option 1: Script automatique (RECOMMANDÉ)
./start.sh

# Option 2: Manuel
# Terminal 1: Backend
cd backend && poetry run uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

**✅ C'est tout ! Ouvrir http://localhost:5173**

---

## 🎮 Utiliser Team Commander

### 1. Se connecter
- Username: `testcommander`
- Password: `TestPassword123!`

### 2. Cliquer "🎮 Team Commander" dans le menu

### 3. Taper une commande naturelle

**Exemples:**

```
"2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"
```

```
"Je veux 10 joueurs. Dans chaque groupe : stabeur, healer, booner, strip, dps"
```

```
"Fais-moi une équipe de 10 avec 2 Firebrands et complète avec du DPS"
```

### 4. ✅ L'IA construit 10 builds optimisés !

**Résultat en 5 secondes :**
- 10 builds complets
- Runes/Sigils optimisés
- Graphiques de performance
- Badge synergie (S/A/B/C)
- Recommandations

---

## 📊 Ce Que Tu Verras

```
┌─────────────────────────────────────────┐
│ 🎮 AI Team Commander                    │
│ Décrivez votre team, l'IA construit... │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 👤 USER: 2 groupes de 5 avec...        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 🤖 AI: ✅ Team créée ! Synergie: A     │
│                                         │
│ ╔═════════════════════════════════════╗ │
│ ║ Équipe de 10   🏆 SYNERGIE A       ║ │
│ ╚═════════════════════════════════════╝ │
│                                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │🛡️Guardian│ │🏹 Ranger │ │💀Necro   ││
│ │Firebrand │ │Druid     │ │Harbinger ││
│ │STAB      │ │HEAL      │ │DPS       ││
│ │          │ │          │ │          ││
│ │Burst: 8K │ │Burst: 23K│ │Burst: 33K││
│ │▓▓░░░░ 21%│ │▓▓▓▓▓░ 59%│ │▓▓▓▓▓▓ 84%││
│ │Survie:3.7│ │Survie:4.2│ │Survie:1.4││
│ └──────────┘ └──────────┘ └──────────┘│
│                                         │
│ 💡 NOTES:                               │
│ ✅ Stabilité: Excellente               │
│ ✅ Soins: Optimaux                     │
│ ⚠️ Cleanse: Faible                    │
└─────────────────────────────────────────┘
```

---

## 🛑 Arrêter

```bash
./stop.sh
```

---

## 🔧 Troubleshooting

### "Backend ne démarre pas"
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### "Frontend ne démarre pas"
```bash
cd frontend
npm install
npm run dev
```

### "Port 8000 déjà utilisé"
```bash
lsof -i :8000  # Trouver le PID
kill -9 <PID>  # Tuer le processus
```

---

## 📚 Docs Complètes

- **Démarrage :** Ce fichier
- **Guide complet :** `README_TEAM_COMMANDER.md`
- **UI Preview :** `UI_PREVIEW.md`
- **Architecture :** `IMPLEMENTATION_COMPLETE_ULTIME.md`
- **Index :** `INDEX_COMPLET.md`

---

## 💡 Tips

### Commandes Courantes
```bash
# Démarrer
./start.sh

# Arrêter
./stop.sh

# Logs backend
tail -f backend.log

# Logs frontend
tail -f frontend.log

# Tests API
cd backend && poetry run python scripts/test_team_commander_api.py
```

### Raccourcis VSCode
- **F5** : Démarrer backend en debug
- **Ctrl+Shift+P** → "Debug: Select and Start Debugging"
- Choisir "🚀 Full Stack" pour démarrer backend + frontend

---

## 🎯 Workflow Typique

1. `./start.sh` → Démarre tout
2. Ouvrir http://localhost:5173
3. Se connecter
4. Cliquer "🎮 Team Commander"
5. Taper commande
6. ✅ Team prête !
7. `./stop.sh` → Arrête tout

**30 secondes du démarrage à la première team ! ⚡**

---

## 🎉 C'est Tout !

**Tu es prêt à créer des teams WvW en parlant naturellement ! 🚀**

**Questions ?** → Voir `INDEX_COMPLET.md` pour tout trouver
