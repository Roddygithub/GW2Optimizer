#!/bin/bash

# Stop any running frontend processes
echo "🔴 Arrêt des processus frontend en cours..."
pkill -f "vite" || true

# Go to frontend directory
cd /home/roddy/GW2Optimizer/frontend

# Clean up
rm -rf node_modules .next .nuxt .cache dist build

# Install dependencies with legacy peer deps
echo "📦 Installation des dépendances..."
npm install --legacy-peer-deps

# Build the project
echo "🔨 Construction du frontend..."
npm run build

# Start the preview server
echo "🚀 Démarrage du serveur de prévisualisation..."
npm run preview

echo "✅ Frontend reconstruit avec succès !"
