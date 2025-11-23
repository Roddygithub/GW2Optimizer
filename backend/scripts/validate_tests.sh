#!/bin/bash

# Script de validation de la suite de tests
# GW2Optimizer v1.2.0

set -e

echo "🧪 Validation de la suite de tests GW2Optimizer v1.2.0"
echo "========================================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
PASSED=0
FAILED=0

# Fonction de vérification
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
    fi
}

# 1. Vérifier la structure des dossiers
echo "📁 Vérification de la structure des dossiers..."
test -d "tests" && test -d "tests/test_services" && test -d "tests/test_api" && test -d "tests/test_integration"
check "Structure des dossiers de tests"

# 2. Vérifier les fichiers de tests
echo ""
echo "📄 Vérification des fichiers de tests..."
test -f "tests/conftest.py"
check "conftest.py"

test -f "tests/test_services/test_build_service.py"
check "test_build_service.py"

test -f "tests/test_services/test_team_service.py"
check "test_team_service.py"

test -f "tests/test_api/test_builds.py"
check "test_builds.py"

test -f "tests/test_api/test_teams.py"
check "test_teams.py"

test -f "tests/test_integration/test_auth_flow.py"
check "test_auth_flow.py"

test -f "tests/test_integration/test_cache_flow.py"
check "test_cache_flow.py"

# 3. Vérifier pytest.ini
echo ""
echo "⚙️  Vérification de la configuration..."
test -f "pytest.ini"
check "pytest.ini"

# 4. Vérifier la configuration Poetry (pyproject.toml)
test -f "pyproject.toml"
check "pyproject.toml (Poetry)"

# 5. Vérifier que pytest est installé
echo ""
echo "📦 Vérification des dépendances..."
python -c "import pytest" 2>/dev/null
check "pytest installé"

python -c "import pytest_asyncio" 2>/dev/null
check "pytest-asyncio installé"

python -c "import pytest_cov" 2>/dev/null
check "pytest-cov installé"

python -c "import httpx" 2>/dev/null
check "httpx installé"

# 6. Compter les tests
echo ""
echo "🔢 Comptage des tests..."
TEST_COUNT=$(pytest --collect-only -q 2>/dev/null | tail -n 1 | grep -oE '[0-9]+' | head -n 1 || echo "0")
if [ "$TEST_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} $TEST_COUNT tests trouvés"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Aucun test trouvé"
    ((FAILED++))
fi

# 7. Vérifier la syntaxe des tests
echo ""
echo "🔍 Vérification de la syntaxe..."
pytest --collect-only -q > /dev/null 2>&1
check "Syntaxe des tests valide"

# 8. Vérifier les workflows GitHub Actions
echo ""
echo "🚀 Vérification des workflows CI/CD..."
test -f "../.github/workflows/ci.yml"
check "Workflow CI configuré"

test -f "../.github/workflows/scheduled-learning.yml"
check "Workflow Learning configuré"

# 9. Vérifier la documentation
echo ""
echo "📚 Vérification de la documentation..."
test -f "../docs/TESTING.md"
check "Documentation TESTING.md"

test -f "../docs/CI_CD_SETUP.md"
check "Documentation CI_CD_SETUP.md"

test -f "../TESTS_AND_CI_IMPLEMENTATION.md"
check "Résumé d'implémentation"

# 10. Exécuter un test rapide
echo ""
echo "🏃 Exécution d'un test rapide..."
pytest tests/test_services/test_build_service.py::TestBuildService::test_create_build_success -v > /dev/null 2>&1
check "Test rapide réussi"

# Résumé
echo ""
echo "========================================================"
echo "📊 Résumé de la validation"
echo "========================================================"
echo -e "${GREEN}Réussis${NC}: $PASSED"
echo -e "${RED}Échoués${NC}: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les tests de validation sont passés !${NC}"
    echo ""
    echo "Prochaines étapes :"
    echo "1. Exécuter la suite complète : pytest"
    echo "2. Vérifier la couverture : pytest --cov=app --cov-report=html"
    echo "3. Pousser vers GitHub pour déclencher CI/CD"
    exit 0
else
    echo -e "${RED}❌ Certaines vérifications ont échoué${NC}"
    echo ""
    echo "Veuillez corriger les erreurs avant de continuer."
    exit 1
fi
