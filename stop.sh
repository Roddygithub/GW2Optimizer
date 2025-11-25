#!/bin/bash

# 🛑 GW2 Optimizer - Script d'Arrêt

echo "════════════════════════════════════════════════════════════════"
echo "🛑 ARRÊT GW2 OPTIMIZER"
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

# Nettoyer les logs si demandé
if [ "$1" = "--clean" ]; then
    echo ""
    echo "🧹 Nettoyage des logs..."
    rm -f backend.log frontend.log
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
