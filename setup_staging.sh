#!/bin/bash

# Définir le répertoire de base du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages d'information
info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Fonction pour afficher les messages de succès
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Fonction pour afficher les erreurs
error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

echo -e "${GREEN}🚀 Démarrage de la configuration du staging GW2Optimizer v4.1.0${NC}"

# 1. Arrêt des services existants
echo -e "\n${GREEN}1/7${NC} Arrêt des services existants..."
pkill -f "uvicorn|vite|npm" || true

# Vérifier si les ports sont disponibles
if lsof -i:8001 -i:5174 | grep -q LISTEN; then
    error "Des processus utilisent déjà les ports 8001 ou 5174. Veuillez les arrêter d'abord."
fi

# 2. Configuration de l'environnement
echo -e "\n${GREEN}2/7${NC} Configuration de l'environnement..."

# Charger les variables d'environnement
if [ -f .env.staging ]; then
    export $(grep -v '^#' .env.staging | xargs)
else
    error "Le fichier .env.staging est introuvable"
fi

# Vérifier les variables d'environnement requises
for var in DATABASE_URL REDIS_URL SECRET_KEY; do
    if [ -z "${!var}" ]; then
        error "La variable d'environnement $var n'est pas définie"
    fi
done

# 3. Nettoyage et préparation
echo -e "\n${GREEN}3/7${NC} Nettoyage et préparation..."

# Créer le répertoire des logs
mkdir -p logs

# Suppression des anciennes bases de données
rm -f staging.db
rm -f /tmp/staging*.log

# Nettoyage du frontend
info "Nettoyage du frontend..."
cd frontend
rm -rf node_modules package-lock.json dist/ .vite/

# 4. Installation des dépendances
echo -e "\n${GREEN}4/7${NC} Installation des dépendances..."

# Backend
info "Installation des dépendances Python..."
cd ..

# Vérifier si poetry est installé
if ! command -v poetry &> /dev/null; then
    info "Poetry n'est pas installé, installation en cours..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Installer les dépendances avec poetry
if [ -f "$PROJECT_DIR/backend/pyproject.toml" ]; then
    cd "$PROJECT_DIR/backend"
    poetry install --no-root
    cd "$PROJECT_DIR"
else
    error "Le fichier pyproject.toml est introuvable dans le répertoire backend"
fi

# Frontend
info "Installation des dépendances Node.js..."
cd frontend
npm install --legacy-peer-deps

# 5. Construction du frontend
echo -e "\n${GREEN}5/7${NC} Construction du frontend..."
npm run build || error "Échec de la construction du frontend"

# 6. Initialisation de la base de données
echo -e "\n${GREEN}6/7${NC} Initialisation de la base de données..."

# Créer la base de données et appliquer les migrations
info "Initialisation de la base de données..."
if [ -f "$PROJECT_DIR/backend/init_db.py" ]; then
    (cd "$PROJECT_DIR/backend" && poetry run python init_db.py) || error "Échec de l'initialisation de la base de données"
else
    error "Le fichier init_db.py est introuvable dans le répertoire backend"
fi

# 7. Démarrage des services
echo -e "\n${GREEN}7/7${NC} Démarrage des services..."

# Démarrer le backend en arrière-plan
info "Démarrage du backend..."
cd "$PROJECT_DIR/backend"
nohup poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 > "$PROJECT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$PROJECT_DIR"

# Démarrer Redis si nécessaire
if ! pgrep -x "redis-server" > /dev/null; then
    info "Démarrage de Redis..."
    redis-server --daemonize yes
fi

# Attendre que le backend soit prêt
info "Attente du démarrage du backend..."
sleep 5

# Vérifier que le backend est en cours d'exécution
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    error "Le backend n'a pas démarré correctement. Voir logs/backend.log pour plus de détails."
fi

# Démarrer le frontend en arrière-plan
info "Démarrage du frontend..."
cd frontend
nohup npm run preview -- --port 5174 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# Attendre que le frontend soit prêt
sleep 3

# Vérification de l'état des services
info "Vérification des services..."

# Vérifier le backend
if curl -s http://localhost:8001/api/v1/health | grep -q "healthy"; then
    success "Backend démarré avec succès sur http://localhost:8001"
else
    error "Erreur lors du démarrage du backend. Voir logs/backend.log pour plus de détails."
fi

# Vérifier le frontend
if curl -s http://localhost:5174 >/dev/null; then
    success "Frontend démarré avec succès sur http://localhost:5174"
else
    error "Erreur lors du démarrage du frontend. Voir logs/frontend.log pour plus de détails."
fi

# Afficher les informations de connexion
echo -e "\n${GREEN}🎉 Configuration du staging terminée avec succès !${NC}"
echo -e "\n🔗 ${YELLOW}Frontend:${NC} http://localhost:5174"
echo -e "🔌 ${YELLOW}Backend:${NC} http://localhost:8001"
echo -e "📊 ${YELLOW}API Docs:${NC} http://localhost:8001/docs"
echo -e "📝 ${YELLOW}Logs:${NC} logs/backend.log et logs/frontend.log"

# Exécuter les tests
echo -e "\n🧪 Exécution des tests de validation..."

# Vérification des endpoints API
endpoints=(
  "/api/v1/health"
  "/api/v1/ai/context"
  "/api/v1/builds/"
  "/api/v1/teams/"
)

# Obtenir un token d'authentification
info "Authentification..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123!")

if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
  TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  success "Authentification réussie"
  
  # Tester les endpoints protégés
  for endpoint in "${endpoints[@]}"; do
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer $TOKEN" \
      "http://localhost:8001$endpoint")
      
    if [ "$status_code" -eq 200 ] || [ "$status_code" -eq 201 ]; then
      echo -e "✅ ${GREEN}GET $endpoint - $status_code${NC}"
    else
      echo -e "❌ ${RED}GET $endpoint - $status_code${NC}"
    fi
  done
  
  # Tester la création d'un build
  info "Test de création d'un build..."
  CREATE_BUILD_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/v1/builds/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name":"Test Build","profession":"Guardian","game_mode":"raid","role":"healer","description":"Test build","is_public":false}')
  
  if echo "$CREATE_BUILD_RESPONSE" | grep -q "id"; then
    success "Création de build réussie"
    BUILD_ID=$(echo "$CREATE_BUILD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    echo -e "   ID du build créé: $BUILD_ID"
  else
    error "Échec de la création du build: $CREATE_BUILD_RESPONSE"
  fi
  
else
  error "Échec de l'authentification: $TOKEN_RESPONSE"
fi

# Afficher les informations de débogage
echo -e "\n${YELLOW}=== Informations de débogage ===${NC}"
echo -e "${YELLOW}Backend:${NC}"
ps aux | grep "uvicorn" | grep -v grep || echo "Aucun processus backend en cours d'exécution"
echo -e "\n${YELLOW}Frontend:${NC}
$(ps aux | grep "vite" | grep -v grep || echo "Aucun processus frontend en cours d'exécution")"

# Afficher les logs en cas d'erreur
if [ -f "logs/backend.log" ]; then
  echo -e "\n${YELLOW}=== Dernières lignes des logs du backend ===${NC}"
  tail -n 10 logs/backend.log
fi

if [ -f "logs/frontend.log" ]; then
  echo -e "\n${YELLOW}=== Dernières lignes des logs du frontend ===${NC}"
  tail -n 10 logs/frontend.log
fi

echo -e "\n${GREEN}✅ Validation terminée avec succès !${NC}"

echo -e "\n${YELLOW}=== Commandes utiles ===${NC}"
echo -e "${YELLOW}Arrêter les services:${NC} pkill -f 'uvicorn|vite|npm'"
echo -e "${YELLOW}Voir les logs du backend:${NC} tail -f logs/backend.log"
echo -e "${YELLOW}Voir les logs du frontend:${NC} tail -f logs/frontend.log"
echo -e "${YELLOW}Accéder à l'interface:${NC} http://localhost:5174"
echo -e "${YELLOW}Documentation de l'API:${NC} http://localhost:8001/docs"
