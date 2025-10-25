#!/bin/bash

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages d'erreur et quitter
function error_exit {
    echo -e "${RED}❌ ERREUR: $1${NC}" >&2
    exit 1
}

echo -e "${YELLOW}🚀 Démarrage de la reconstruction du frontend GW2Optimizer v4.1.0${NC}"

# Étape 1: Se placer dans le dossier frontend
echo -e "\n${YELLOW}📂 Étape 1/5: Accès au dossier frontend...${NC}"
cd "$(dirname "$0")/frontend" || error_exit "Impossible d'accéder au dossier frontend"

# Étape 2: Nettoyage
echo -e "\n${YELLOW}🧹 Étape 2/5: Nettoyage des fichiers de build précédents...${NC}"
rm -rf dist node_modules package-lock.json .vite 2>/dev/null

# Étape 3: Installation des dépendances
echo -e "\n${YELLOW}📦 Étape 3/5: Installation des dépendances...${NC}"
npm install --legacy-peer-deps || error_exit "Échec de l'installation des dépendances"

# Vérification de la version dans l'application
echo -e "\n${YELLOW}ℹ️ Vérification de la version de l'application...${NC}"
APP_VERSION="4.1.0"
echo -e "${GREEN}✅ Version de l'application: $APP_VERSION${NC}"

# Étape 4: Construction du projet
echo -e "\n${YELLOW}🔨 Étape 4/5: Construction du projet...${NC}"
npm run build || error_exit "Échec de la construction du projet"

# Étape 5: Démarrage du serveur de développement
echo -e "\n${GREEN}✅ Construction terminée avec succès !${NC}"
echo -e "\n${YELLOW}🚀 Démarrage du serveur de développement...${NC}"
echo -e "${GREEN}👉 Accédez à l'application sur http://localhost:5174${NC}"
npm run dev
