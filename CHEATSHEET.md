# 📋 CHEATSHEET - Team Commander

> **Aide-mémoire rapide pour toutes les commandes**

---

## 🚀 DÉMARRAGE / ARRÊT

```bash
./start.sh              # Démarre TOUT (backend + frontend + redis)
./stop.sh               # Arrête TOUT proprement
./stop.sh --clean       # Arrête + nettoie les logs

# Manuel
cd backend && poetry run uvicorn app.main:app --reload
cd frontend && npm run dev
```

---

## 🎮 EXEMPLES DE COMMANDES IA

### Par Classes (Fixé)
```
2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper
```

### Par Rôles (Flexible)
```
Je veux 10 joueurs. Dans chaque groupe : stabeur, healer, booner, strip, dps
```

### Mix (Classes + Rôles)
```
Fais-moi une équipe avec 2 Firebrands, 2 Druids, et complète avec du DPS
```

### Variations
```
Une équipe de 10 pour WvW zerg avec bonne stabilité
Un groupe de 5 optimisé pour outnumber
2 groupes avec focus sur le burst damage
```

---

## 🔧 COMMANDES BACKEND

```bash
cd backend

# Démarrer
poetry run uvicorn app.main:app --reload

# Tests
poetry run python scripts/test_team_commander_api.py
poetry run pytest tests/ -v

# Shell interactif
poetry shell

# Installer dépendances
poetry install
poetry add <package>
```

---

## 🎨 COMMANDES FRONTEND

```bash
cd frontend

# Démarrer dev
npm run dev

# Build production
npm run build

# Preview production
npm run preview

# Installer dépendances
npm install
npm add <package>

# Linter
npm run lint
```

---

## 🐛 DEBUG

### Logs
```bash
tail -f backend.log      # Logs backend en temps réel
tail -f frontend.log     # Logs frontend en temps réel
cat backend.log | grep ERROR   # Chercher erreurs
```

### Ports
```bash
lsof -i :8000            # Qui utilise port 8000 (backend)
lsof -i :5173            # Qui utilise port 5173 (frontend)
kill -9 <PID>            # Tuer un processus
```

### Redis
```bash
docker ps | grep redis   # Redis actif ?
docker start gw2optimizer-redis-1   # Démarrer
docker logs gw2optimizer-redis-1    # Logs
```

### Database
```bash
cd backend
poetry run python -c "from app.db.init_db import init_db; import asyncio; asyncio.run(init_db())"
```

---

## 📊 TESTS

### Backend
```bash
cd backend

# Test Team Commander API
poetry run python scripts/test_team_commander_api.py

# Tous les tests
poetry run pytest tests/ -v

# Test spécifique
poetry run pytest tests/test_services/test_team_commander.py -v
```

---

## 🔍 RECHERCHE DANS LE CODE

### Backend
```bash
cd backend

# Trouver tous les endpoints
grep -r "@router" app/api/

# Trouver Agent classes
find app/agents -name "*.py" -exec grep "class.*Agent" {} \;

# Trouver ModifierType usage
grep -r "ModifierType\." app/engine/
```

### Frontend
```bash
cd frontend

# Trouver composants
find src/components -name "*.tsx"

# Trouver tous les services
find src/services -name "*.ts"
```

---

## 🗂️ FICHIERS IMPORTANTS

### Backend
```
app/agents/team_commander_agent.py    # Agent IA principal
app/api/team_commander.py             # API endpoint
app/engine/gear/registry.py           # 62 runes/sigils
app/main.py                            # Router config
```

### Frontend
```
src/pages/TeamCommander.tsx            # Page principale
src/components/TeamDisplay.tsx         # Affichage team
src/services/teamCommander.service.ts  # API calls
```

### Docs
```
QUICKSTART.md                          # Démarrage rapide
INDEX_COMPLET.md                       # Index de tout
README_TEAM_COMMANDER.md               # Guide complet
SESSION_FINALE_RECAP.md                # Résumé session
```

---

## 🌐 URLs

```
Frontend:    http://localhost:5173
Backend:     http://localhost:8000
API Docs:    http://localhost:8000/docs
Health:      http://localhost:8000/health
Metrics:     http://localhost:8000/metrics
```

---

## 🔑 AUTH

### User de Test
```
Username: testcommander
Password: TestPassword123!
```

### Obtenir Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=testcommander&password=TestPassword123!"
```

### Utiliser Token
```bash
TOKEN="<your_token>"
curl -X POST http://localhost:8000/api/v1/ai/teams/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "2 groupes de 5 avec Firebrand..."}'
```

---

## 📦 REGISTRY ITEMS

### Runes (27)
```
Power:   Scholar, Eagle, Hoelbrak, Flock, Scavenging, Ranger, Pack, Vampirism
Condi:   Nightmare, Fireworks, Trooper, Balthazar, Afflicted
Support: Monk, Water, Druid, Strength, Aristocracy, Chronomancer, Herald
Tank:    Durability, Ogre, Dolyak, Antitoxin
```

### Sigils (35)
```
Power:   Force, Impact, Bloodlust, Air, Accuracy, Perception, Luck
Condi:   Bursting, Hydromancy, Doom, Earth, Fire, Ice, Geomancy, Torment, Malice, Agony
Support: Energy, Strength, Concentration, Generosity
Tank:    Absorption, Leeching, Transference, Draining
```

---

## 🎨 CLASSES & ICÔNES

```
🛡️ Guardian      (Firebrand, Willbender)
⚔️ Warrior       (Spellbreaker, Berserker)
🌊 Revenant      (Herald, Renegade)
🔧 Engineer      (Scrapper, Holosmith, Mechanist)
🏹 Ranger        (Druid, Soulbeast)
🗡️ Thief         (Deadeye, Daredevil, Specter)
🔥 Elementalist  (Tempest, Weaver, Catalyst)
✨ Mesmer        (Chronomancer, Mirage, Virtuoso)
💀 Necromancer   (Reaper, Scourge, Harbinger)
```

---

## 🎯 RÔLES

```
🛡️ Stab     - Stabilité (Firebrand, Chronomancer)
❤️ Heal     - Soins (Druid, Scrapper, Tempest)
⚡ Boon     - Boon share (Herald, Chronomancer)
🎯 Strip    - Boon strip (Spellbreaker, Scourge)
⚔️ DPS      - Damage (Reaper, Harbinger, Berserker)
💊 Cleanse  - Condi cleanse (Scrapper, Druid)
💜 Support  - Support général (Firebrand, Druid)
```

---

## 🏆 SYNERGY SCORES

```
S - Excellent    (gradient jaune→orange)
A - Très bon     (gradient vert→émeraude)
B - Bon          (gradient bleu→cyan)
C - Acceptable   (gradient gris→slate)
```

---

## 🔥 SHORTCUTS CLAVIER

### VSCode
```
F5                      - Debug backend
Ctrl+Shift+D            - Debug panel
Ctrl+Shift+P            - Command palette
Ctrl+`                  - Terminal
```

### Browser
```
Ctrl+Shift+I            - DevTools
F12                     - DevTools
Ctrl+Shift+R            - Hard refresh
```

---

## 💡 TIPS & TRICKS

### Backend Plus Rapide
```bash
# Utiliser uvloop pour 30-40% plus rapide
poetry add uvloop
# Puis dans main.py: import uvloop; uvloop.install()
```

### Frontend Plus Rapide
```bash
# Build optimisé
npm run build
npm run preview  # Test le build
```

### Redis Cache Hit Rate
```bash
docker exec gw2optimizer-redis-1 redis-cli INFO stats | grep keyspace
```

---

## 🎉 QUICK WINS

**Créer une team en 3 commandes:**
```bash
./start.sh
# Ouvrir http://localhost:5173
# Taper: "2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"
```

**Tester l'API en 1 commande:**
```bash
cd backend && poetry run python scripts/test_team_commander_api.py
```

**Voir tous les logs en temps réel:**
```bash
tail -f backend.log frontend.log
```

---

## 📞 AIDE RAPIDE

**Problème ?** → Voir la section dans `INDEX_COMPLET.md`

**Besoin d'un guide ?** → `README_TEAM_COMMANDER.md`

**Juste démarrer ?** → `QUICKSTART.md`

**Voir l'UI ?** → `UI_PREVIEW.md`

---

**✅ Ce cheatsheet couvre 95% des besoins quotidiens ! 🚀**
