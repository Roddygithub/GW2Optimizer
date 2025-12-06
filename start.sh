#!/bin/bash

# 🚀 GW2 Optimizer - Script de Démarrage (Backend + Frontend + Redis optionnel)

echo "════════════════════════════════════════════════════════════════"
echo "🚀 GW2 OPTIMIZER - AI DASHBOARD & TEAM COMMANDER"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Vérifier si on est dans le bon dossier
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur: Ce script doit être lancé depuis le dossier GW2Optimizer/"
    exit 1
fi

# 1. Démarrer Redis (si Docker)
echo "🔌 Vérification Redis..."
if command -v docker &> /dev/null; then
    if docker ps | grep -q gw2optimizer-redis; then
        echo "✅ Redis déjà en cours d'exécution"
    else
        echo "🚀 Démarrage Redis..."
        docker start gw2optimizer-redis-1 2>/dev/null || docker-compose up -d redis 2>/dev/null || echo "⚠️ Redis non trouvé (OK si pas besoin)"
    fi
else
    echo "⚠️ Docker non installé (OK si Redis local)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🧠 LLM / OLLAMA"
echo "════════════════════════════════════════════════════════════════"
echo ""

if command -v ollama &> /dev/null; then
    if pgrep -x "ollama" > /dev/null 2>&1; then
        echo "✅ Ollama déjà en cours d'exécution"
    else
        echo "🚀 Démarrage du serveur Ollama (ollama serve)..."
        ollama serve > ollama.log 2>&1 &
        OLLAMA_PID=$!
        echo "✅ Ollama démarré (PID: $OLLAMA_PID)"
        echo "$OLLAMA_PID" > .ollama.pid
    fi
else
    echo "⚠️ Ollama non installé - les fonctionnalités IA (synergie, Team Commander, Build Lab) ne fonctionneront pas."
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔧 BACKEND"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 2. Backend
cd backend

# Vérifier Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry non installé !"
    echo "   Installer avec: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Installer dépendances si nécessaire
if [ ! -d ".venv" ]; then
    echo "📦 Installation des dépendances backend..."
    poetry install
fi

# Démarrer le backend en background
echo "🚀 Démarrage du backend (port 8000)..."
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend démarré (PID: $BACKEND_PID)"
echo "   Logs: tail -f backend.log"

cd ..

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🎨 FRONTEND"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 3. Frontend
cd frontend

# Vérifier npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm non installé !"
    exit 1
fi

# Installer dépendances si nécessaire
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances frontend..."
    npm install
fi

# Démarrer le frontend en background
echo "🚀 Démarrage du frontend (port 5173)..."
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend démarré (PID: $FRONTEND_PID)"
echo "   Logs: tail -f frontend.log"

cd ..

# Sauvegarder les PIDs
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ DÉMARRAGE COMPLET !"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Application disponible dans ~10 secondes:"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Pour consulter le Meta Dashboard (archétypes & méta):"
echo "   1. Ouvrir http://localhost:5173"
echo "   2. Se connecter"
echo "   3. Cliquer sur 'Méta' dans le menu de gauche"
echo "   4. Choisir un mode de jeu (ex: WvW Zerg)"
echo ""
echo "🎮 Pour utiliser Team Commander:"
echo "   1. Ouvrir http://localhost:5173"
echo "   2. Se connecter"
echo "   3. Cliquer sur '🎮 Team Commander'"
echo "   4. Taper une commande naturelle"
echo ""
echo "📝 Exemples de commandes Team Commander:"
echo "   • 2 groupes de 5 avec Firebrand, Druid, Harbinger..."
echo "   • Je veux 10 joueurs avec stabeur, healer, booner..."
echo ""
echo "📊 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Pour arrêter:"
echo "   ./stop.sh"
echo ""
echo "════════════════════════════════════════════════════════════════"

# Attendre un peu pour voir les erreurs de démarrage
sleep 3

# Vérifier si les processus tournent
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: Erreur de démarrage (voir backend.log)"
fi

if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: Erreur de démarrage (voir frontend.log)"
fi

echo ""
echo "🎉 Prêt à utiliser !"
