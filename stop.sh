#!/bin/bash

# 🛑 GW2 Optimizer - Script d'Arrêt (Backend + Frontend)

echo "════════════════════════════════════════════════════════════════"
echo "🛑 ARRÊT GW2 OPTIMIZER - AI DASHBOARD & TEAM COMMANDER"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Vérifier si on est dans le bon dossier
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Erreur: Ce script doit être lancé depuis le dossier GW2Optimizer/"
    exit 1
fi

STOPPED=0

# Arrêter le backend
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🛑 Arrêt du backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || kill -9 $BACKEND_PID 2>/dev/null
        echo "✅ Backend arrêté"
        STOPPED=1
    else
        echo "⚠️ Backend déjà arrêté"
    fi
    rm .backend.pid
else
    # Fallback : chercher tous les processus uvicorn
    echo "🔍 Recherche processus backend..."
    pkill -f "uvicorn app.main:app" && echo "✅ Backend arrêté" && STOPPED=1
fi

# Arrêter le frontend
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🛑 Arrêt du frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || kill -9 $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend arrêté"
        STOPPED=1
    else
        echo "⚠️ Frontend déjà arrêté"
    fi
    rm .frontend.pid
else
    # Fallback : chercher tous les processus vite
    echo "🔍 Recherche processus frontend..."
    pkill -f "vite" && echo "✅ Frontend arrêté" && STOPPED=1
fi

# Arrêter Ollama (LLM)
if [ -f ".ollama.pid" ]; then
    OLLAMA_PID=$(cat .ollama.pid)
    if ps -p $OLLAMA_PID > /dev/null 2>&1; then
        echo "🛑 Arrêt d'Ollama (PID: $OLLAMA_PID)..."
        kill $OLLAMA_PID 2>/dev/null || kill -9 $OLLAMA_PID 2>/dev/null
        echo "✅ Ollama arrêté"
        STOPPED=1
    else
        echo "⚠️ Ollama déjà arrêté"
    fi
    rm .ollama.pid
else
    # Fallback : chercher le processus ollama serve
    if command -v ollama &> /dev/null; then
        echo "🔍 Recherche processus Ollama..."
        pkill -f "ollama serve" && echo "✅ Ollama arrêté" && STOPPED=1 || echo "⚠️ Aucun processus Ollama trouvé"
    fi
fi

# Nettoyer les logs si demandé
if [ "$1" = "--clean" ]; then
    echo ""
    echo "🧹 Nettoyage des logs..."
    rm -f backend.log frontend.log ollama.log
    echo "✅ Logs supprimés"
fi

echo ""
if [ $STOPPED -eq 1 ]; then
    echo "✅ Tous les services sont arrêtés"
else
    echo "⚠️ Aucun service en cours d'exécution"
fi
echo ""
echo "════════════════════════════════════════════════════════════════"
