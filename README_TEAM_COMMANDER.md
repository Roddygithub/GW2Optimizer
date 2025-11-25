# 🎮 GW2 Optimizer - Team Commander

> L'IA qui construit vos teams WvW automatiquement. **Zéro clic. Juste parler.**

---

## ⚡ Quick Start

### Lancer l'app
```bash
# Backend
cd backend && poetry run uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Utiliser
1. Ouvrir http://localhost:5173
2. Se connecter
3. Cliquer **🎮 Team Commander**
4. Taper une commande :
   ```
   "2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"
   ```
5. ✅ L'IA construit 10 builds optimisés !

---

## 🎯 Exemples de Commandes

### Par Classes
```
"2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"
```

### Par Rôles
```
"Je veux 10 joueurs. Dans chaque groupe : stabeur, healer, booner, strip, dps"
```

### Mix
```
"Fais-moi une équipe avec 2 Firebrands, 2 Druids, et complète avec du DPS"
```

---

## ✨ Features

### 🤖 AI Team Commander
- Parse langage naturel
- Optimise runes/sigils automatiquement
- Analyse synergie (S/A/B/C)
- Génère recommandations

### 🎨 UI Moderne
- **Cartes de build** avec stats complètes
- **Icônes de classes** (🛡️⚔️🌊🔧🏹🗡️🔥✨💀)
- **Graphiques performance** (Burst, Survie)
- **Badge synergie** (S/A/B/C coloré)
- **Responsive** (mobile/tablet/desktop)

### 📊 Analytics
- Performance par slot (DPS, Survie)
- Synergie globale (Stab, Heal, Boon, Strip)
- Recommandations personnalisées

---

## 📁 Structure

```
GW2Optimizer/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── team_commander_agent.py  ⭐ Agent IA
│   │   ├── api/
│   │   │   └── team_commander.py        ⭐ API endpoint
│   │   └── engine/gear/
│   │       └── registry.py              ⭐ 62 items WvW
│   └── scripts/
│       └── test_team_commander_api.py   ⭐ Tests auto
├── frontend/
│   └── src/
│       ├── pages/
│       │   └── TeamCommander.tsx        ⭐ Page principale
│       ├── components/
│       │   └── TeamDisplay.tsx          ⭐ Affichage team
│       └── services/
│           └── teamCommander.service.ts ⭐ API calls
└── docs/
    ├── SESSION_FINALE_RECAP.md          📖 Résumé complet
    ├── UI_PREVIEW.md                    🎨 Preview UI
    └── NETTOYAGE_CODE_COMPLETE.md       🧹 Optimisations
```

---

## 🔧 API

### Endpoint
```
POST /api/v1/ai/teams/command
```

### Request
```json
{
  "message": "Je veux 2 groupes de 5 avec Firebrand, Druid..."
}
```

### Response
```json
{
  "success": true,
  "team_size": 10,
  "groups": [
    {
      "index": 1,
      "slots": [
        {
          "role": "stab",
          "profession": "Guardian",
          "specialization": "Firebrand",
          "equipment": {
            "stats": "Minstrel",
            "rune": "Monk",
            "sigils": ["Force", "Energy"]
          },
          "performance": {
            "burst_damage": 8562,
            "survivability": 3.7,
            "dps_increase": 18.2
          }
        }
        // ... 4 autres slots
      ]
    }
    // ... groupe 2
  ],
  "synergy": {
    "score": "A",
    "details": {
      "stability": "Excellent",
      "healing": "Optimal",
      "boon_share": "Perfect",
      "boon_strip": "Effective",
      "damage": "High",
      "cleanse": "Weak"
    }
  },
  "notes": [
    "✅ Couverture Stabilité excellente",
    "✅ Soins optimaux",
    "⚠️ Faible cleanse - Vulnérable aux condi"
  ]
}
```

---

## 📊 Registry WvW

### Runes (27 total)
**Power DPS:** Scholar, Eagle, Hoelbrak, Flock, Scavenging, Ranger, Pack, Vampirism  
**Condi DPS:** Nightmare, Fireworks, Trooper, Balthazar, Afflicted  
**Support/Heal:** Monk, Water, Druid, Strength, Aristocracy, Chronomancer, Herald  
**Tank/Bruiser:** Durability, Ogre, Dolyak, Antitoxin  

### Sigils (35 total)
**Power DPS:** Force, Impact, Bloodlust, Air, Accuracy, Perception, Luck  
**Condi DPS:** Bursting, Hydromancy, Doom, Earth, Fire, Ice, Geomancy, etc.  
**Support:** Energy, Strength, Concentration, Generosity  
**Tank/Sustain:** Absorption, Leeching, Transference, Draining  

---

## 🧪 Tests

### Backend
```bash
cd backend
poetry run python scripts/test_team_commander_api.py
```

### Résultats Attendus
```
✅ Test 1: Classes figées - PASS (200 OK, Synergie A)
✅ Test 2: Par rôles - PASS (200 OK, Synergie A)
```

---

## 🎨 UI Components

### Cartes de Build
- Icône classe (🛡️⚔️🌊)
- Badge rôle (coloré)
- Stats (Minstrel, Berserker, etc.)
- Rune + Sigils
- Graphiques performance

### Badge Synergie
- **S:** Gradient jaune→orange ⭐⭐⭐
- **A:** Gradient vert→émeraude ⭐⭐
- **B:** Gradient bleu→cyan ⭐
- **C:** Gradient gris→slate

### Graphiques
- **Burst Damage:** Barre orange (0-40K)
- **Survivability:** Barre cyan (0-5.0)

---

## 💡 Pourquoi C'est Révolutionnaire ?

### Avant (Traditionnel)
1. Ouvrir formulaire
2. Choisir classe → dropdown
3. Choisir rune → dropdown
4. Choisir sigils → 2 dropdowns
5. **Répéter 10 fois**
6. **= 50+ clics**

### Maintenant (AI Commander)
1. Taper une phrase
2. **= 1 action**
3. ✅ L'IA fait TOUT

**Gain de temps : 95% !**

---

## 📚 Documentation

### Guides
- [SESSION_FINALE_RECAP.md](SESSION_FINALE_RECAP.md) - Résumé complet
- [UI_PREVIEW.md](UI_PREVIEW.md) - Preview UI visuel
- [NETTOYAGE_CODE_COMPLETE.md](NETTOYAGE_CODE_COMPLETE.md) - Optimisations
- [REPONSES_COMPLETES.md](REPONSES_COMPLETES.md) - FAQ détaillée

### Technique
- [IMPLEMENTATION_COMPLETE_ULTIME.md](IMPLEMENTATION_COMPLETE_ULTIME.md) - Guide technique
- [QUICK_START_NEW_FEATURES.md](QUICK_START_NEW_FEATURES.md) - Features précédentes

---

## 🚀 Roadmap

### ✅ Fait
- [x] Registry 100% (62 items WvW)
- [x] Team Commander Agent (backend)
- [x] UI moderne complète (frontend)
- [x] Tests automatisés
- [x] Documentation exhaustive

### ⏳ Court Terme
- [ ] Persister teams (SavedTeam model)
- [ ] Export team (JSON/PNG)
- [ ] Partage team (URL)

### 💡 Long Terme
- [ ] MetaGPT multi-agent
- [ ] ChromaDB semantic search
- [ ] Real-time collaboration
- [ ] DPS rotation simulation

---

## 🤝 Contributing

Le projet est open-source. Contributions bienvenues !

### Development
```bash
# Backend
cd backend
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Standards
- Backend : Python 3.13+, FastAPI, async/await
- Frontend : TypeScript, React, Tailwind
- Type hints : 95%+
- Tests : Pytest (backend), Jest (frontend)

---

## 📜 License

MIT License - Open Source

---

## 💬 Support

Issues : GitHub Issues  
Docs : Documentation complète dans `/docs`

---

## 🎉 Credits

**Développé avec ❤️ pour la communauté GW2 WvW**

---

**🚀 L'UTILISATEUR NE CLIQUE PLUS. IL PARLE. C'EST LE FUTUR ! ✨**
