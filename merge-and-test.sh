#!/bin/bash
set -e  # Arrêt immédiat en cas d'erreur

echo "======================================"
echo "🚀 Merge Feature to Main + CI Validation"
echo "======================================"

# Couleurs pour les logs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
REPO_ROOT="/home/roddy/GW2Optimizer"
FEATURE_BRANCH=$(git branch --show-current)
TARGET_BRANCH="main"

cd "$REPO_ROOT"

echo -e "${YELLOW}📋 Branche courante: ${FEATURE_BRANCH}${NC}"

# Étape 1: S'assurer que tout est commité
echo ""
echo "======================================"
echo "Étape 1: Vérification des changements non commités"
echo "======================================"

if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️  Changements non commités détectés. Commit automatique...${NC}"
    git add .
    git commit -m "Finalize AI Build Lab, AnalystAgent fallback, Hardstuck scraper and validation improvements"
    echo -e "${GREEN}✅ Changements commités${NC}"
else
    echo -e "${GREEN}✅ Aucun changement non commité${NC}"
fi

# Étape 2: Checkout main et pull
echo ""
echo "======================================"
echo "Étape 2: Checkout ${TARGET_BRANCH} et mise à jour"
echo "======================================"

git checkout "$TARGET_BRANCH"
git pull origin "$TARGET_BRANCH" || echo -e "${YELLOW}⚠️  Pull échoué (peut-être pas de remote configuré), on continue...${NC}"

# Étape 3: Merge de la feature branch
echo ""
echo "======================================"
echo "Étape 3: Merge de ${FEATURE_BRANCH} dans ${TARGET_BRANCH}"
echo "======================================"

if git merge "$FEATURE_BRANCH" --no-edit; then
    echo -e "${GREEN}✅ Merge réussi sans conflit${NC}"
else
    echo -e "${RED}❌ CONFLITS DÉTECTÉS${NC}"
    echo "Résous les conflits manuellement, puis relance ce script."
    exit 1
fi

# Étape 4: Boucle de validation CI Docker
echo ""
echo "======================================"
echo "Étape 4: Validation CI avec Docker Compose"
echo "======================================"

MAX_ATTEMPTS=5
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo ""
    echo -e "${YELLOW}🔄 Tentative ${ATTEMPT}/${MAX_ATTEMPTS} - Lancement des tests Docker...${NC}"
    
    if docker compose -f docker-compose.test.yml up --build --abort-on-container-exit; then
        echo ""
        echo -e "${GREEN}✅✅✅ TOUS LES TESTS SONT VERTS ! ✅✅✅${NC}"
        
        # Étape 5: Push vers origin/main
        echo ""
        echo "======================================"
        echo "Étape 5: Push vers origin/${TARGET_BRANCH}"
        echo "======================================"
        
        git push origin "$TARGET_BRANCH"
        
        echo ""
        echo -e "${GREEN}======================================"
        echo "🎉 SUCCÈS COMPLET 🎉"
        echo "======================================"
        echo "✅ Merge effectué: ${FEATURE_BRANCH} → ${TARGET_BRANCH}"
        echo "✅ Tests Docker: 100% PASS"
        echo "✅ Push vers origin/${TARGET_BRANCH}: OK"
        echo -e "======================================${NC}"
        
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Tests échoués (tentative ${ATTEMPT}/${MAX_ATTEMPTS})${NC}"
        
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            echo ""
            echo -e "${RED}======================================"
            echo "❌ ÉCHEC APRÈS ${MAX_ATTEMPTS} TENTATIVES"
            echo "======================================"
            echo "Les tests Docker échouent toujours."
            echo "Analyse les logs ci-dessus pour identifier les erreurs."
            echo "Corrige le code, puis relance ce script."
            echo -e "======================================${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${YELLOW}⚠️  Pause de 5 secondes avant la prochaine tentative...${NC}"
        echo "Si tu veux corriger du code maintenant, interromps (Ctrl+C) et relance après correction."
        sleep 5
        
        ATTEMPT=$((ATTEMPT + 1))
    fi
done
