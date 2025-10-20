#!/bin/bash

# Script d'exécution des tests avec différentes options
# GW2Optimizer v1.2.0

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🧪 GW2Optimizer - Suite de tests v1.2.0${NC}"
echo "========================================================"
echo ""

# Fonction d'aide
show_help() {
    echo "Usage: ./scripts/run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  all           Exécuter tous les tests (par défaut)"
    echo "  unit          Tests unitaires uniquement"
    echo "  api           Tests d'API uniquement"
    echo "  integration   Tests d'intégration uniquement"
    echo "  coverage      Tests avec rapport de couverture HTML"
    echo "  fast          Tests rapides (sans intégration)"
    echo "  watch         Mode watch (re-exécution automatique)"
    echo "  parallel      Tests en parallèle"
    echo "  verbose       Tests avec sortie détaillée"
    echo "  help          Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  ./scripts/run_tests.sh"
    echo "  ./scripts/run_tests.sh unit"
    echo "  ./scripts/run_tests.sh coverage"
}

# Déterminer l'option
OPTION=${1:-all}

case $OPTION in
    all)
        echo -e "${GREEN}📋 Exécution de tous les tests${NC}"
        pytest --cov=app --cov-report=term-missing
        ;;
    
    unit)
        echo -e "${GREEN}🔬 Tests unitaires (services)${NC}"
        pytest tests/test_services/ -v
        ;;
    
    api)
        echo -e "${GREEN}🌐 Tests d'API${NC}"
        pytest tests/test_api/ -v
        ;;
    
    integration)
        echo -e "${GREEN}🔗 Tests d'intégration${NC}"
        pytest tests/test_integration/ -v -m integration
        ;;
    
    coverage)
        echo -e "${GREEN}📊 Tests avec couverture HTML${NC}"
        pytest --cov=app --cov-report=html --cov-report=term
        echo ""
        echo -e "${BLUE}Rapport de couverture généré dans htmlcov/index.html${NC}"
        ;;
    
    fast)
        echo -e "${GREEN}⚡ Tests rapides (sans intégration)${NC}"
        pytest -m "not integration" -v
        ;;
    
    watch)
        echo -e "${GREEN}👁️  Mode watch activé${NC}"
        pytest-watch
        ;;
    
    parallel)
        echo -e "${GREEN}🚀 Tests en parallèle${NC}"
        pytest -n auto --cov=app --cov-report=term
        ;;
    
    verbose)
        echo -e "${GREEN}📢 Tests avec sortie détaillée${NC}"
        pytest -vv --tb=long
        ;;
    
    help)
        show_help
        exit 0
        ;;
    
    *)
        echo -e "${YELLOW}⚠️  Option inconnue: $OPTION${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

# Vérifier le code de sortie
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Tests terminés avec succès !${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Certains tests ont échoué${NC}"
    exit 1
fi
