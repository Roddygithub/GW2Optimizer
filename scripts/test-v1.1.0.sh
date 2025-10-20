#!/bin/bash

# Script de validation GW2Optimizer v1.1.0
# Tests des nouvelles fonctionnalités Meta Analysis

set -e

echo "🚀 GW2Optimizer v1.1.0 - Validation Script"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
PASSED=0
FAILED=0

# Fonction de test
test_command() {
    local description=$1
    local command=$2
    
    echo -n "Testing: $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "📦 Step 1: Environment Check"
echo "----------------------------"

# Vérifier Python
test_command "Python 3.11+" "python3 --version | grep -E 'Python 3\.(11|12)'"

# Vérifier les dépendances
test_command "Backend dependencies" "cd backend && pip list | grep -q fastapi"

echo ""
echo "🧪 Step 2: Unit Tests"
echo "---------------------"

cd backend

# Tests Meta Agent
test_command "Meta Agent tests" "pytest tests/test_meta_agent.py -v --tb=short"

# Tests GW2 API Client
test_command "GW2 API Client tests" "pytest tests/test_gw2_api_client.py -v --tb=short"

# Tests Meta Analysis Workflow
test_command "Meta Analysis Workflow tests" "pytest tests/test_meta_analysis_workflow.py -v --tb=short"

# Tous les tests v1.1.0
test_command "All v1.1.0 tests" "pytest tests/test_meta_*.py -v"

echo ""
echo "📊 Step 3: Code Quality"
echo "-----------------------"

# Vérifier les imports
test_command "Import validation" "python3 -c 'from app.agents.meta_agent import MetaAgent; from app.services.gw2_api_client import GW2APIClient; from app.workflows.meta_analysis_workflow import MetaAnalysisWorkflow'"

# Vérifier la syntaxe
test_command "Syntax check (meta_agent)" "python3 -m py_compile app/agents/meta_agent.py"
test_command "Syntax check (gw2_api_client)" "python3 -m py_compile app/services/gw2_api_client.py"
test_command "Syntax check (meta_workflow)" "python3 -m py_compile app/workflows/meta_analysis_workflow.py"
test_command "Syntax check (meta API)" "python3 -m py_compile app/api/meta.py"

echo ""
echo "🔍 Step 4: Integration Check"
echo "----------------------------"

# Vérifier que les modules sont bien intégrés
test_command "Agents module integration" "python3 -c 'from app.agents import MetaAgent; assert MetaAgent is not None'"
test_command "Workflows module integration" "python3 -c 'from app.workflows import MetaAnalysisWorkflow; assert MetaAnalysisWorkflow is not None'"

# Vérifier que le router est bien inclus
test_command "API router integration" "grep -q 'from app.api import.*meta' app/main.py"
test_command "Meta router included" "grep -q 'meta.router' app/main.py"

echo ""
echo "📝 Step 5: Documentation Check"
echo "------------------------------"

cd ..

# Vérifier que la documentation existe
test_command "META_ANALYSIS.md exists" "test -f docs/META_ANALYSIS.md"
test_command "CHANGELOG updated" "grep -q '## \[1.1.0\]' CHANGELOG.md"
test_command "Release summary exists" "test -f RELEASE_v1.1.0_SUMMARY.md"

# Vérifier la taille des fichiers
test_command "META_ANALYSIS.md size" "test $(wc -l < docs/META_ANALYSIS.md) -gt 300"
test_command "CHANGELOG v1.1.0 section" "test $(grep -A 100 '## \[1.1.0\]' CHANGELOG.md | wc -l) -gt 50"

echo ""
echo "🏗️ Step 6: File Structure"
echo "-------------------------"

# Vérifier que tous les fichiers existent
test_command "meta_agent.py exists" "test -f backend/app/agents/meta_agent.py"
test_command "gw2_api_client.py exists" "test -f backend/app/services/gw2_api_client.py"
test_command "meta_analysis_workflow.py exists" "test -f backend/app/workflows/meta_analysis_workflow.py"
test_command "meta.py API exists" "test -f backend/app/api/meta.py"
test_command "test_meta_agent.py exists" "test -f backend/tests/test_meta_agent.py"
test_command "test_gw2_api_client.py exists" "test -f backend/tests/test_gw2_api_client.py"
test_command "test_meta_analysis_workflow.py exists" "test -f backend/tests/test_meta_analysis_workflow.py"

echo ""
echo "📈 Step 7: Code Statistics"
echo "-------------------------"

# Compter les lignes de code
META_AGENT_LINES=$(wc -l < backend/app/agents/meta_agent.py)
GW2_CLIENT_LINES=$(wc -l < backend/app/services/gw2_api_client.py)
META_WORKFLOW_LINES=$(wc -l < backend/app/workflows/meta_analysis_workflow.py)
META_API_LINES=$(wc -l < backend/app/api/meta.py)

echo "Meta Agent:              $META_AGENT_LINES lines"
echo "GW2 API Client:          $GW2_CLIENT_LINES lines"
echo "Meta Analysis Workflow:  $META_WORKFLOW_LINES lines"
echo "Meta API:                $META_API_LINES lines"

TOTAL_NEW_LINES=$((META_AGENT_LINES + GW2_CLIENT_LINES + META_WORKFLOW_LINES + META_API_LINES))
echo "Total new code:          $TOTAL_NEW_LINES lines"

# Compter les tests
TEST_META_AGENT=$(grep -c "async def test_" backend/tests/test_meta_agent.py || echo 0)
TEST_GW2_CLIENT=$(grep -c "async def test_" backend/tests/test_gw2_api_client.py || echo 0)
TEST_META_WORKFLOW=$(grep -c "async def test_" backend/tests/test_meta_analysis_workflow.py || echo 0)

echo ""
echo "Test Meta Agent:         $TEST_META_AGENT tests"
echo "Test GW2 API Client:     $TEST_GW2_CLIENT tests"
echo "Test Meta Workflow:      $TEST_META_WORKFLOW tests"

TOTAL_TESTS=$((TEST_META_AGENT + TEST_GW2_CLIENT + TEST_META_WORKFLOW))
echo "Total new tests:         $TOTAL_TESTS tests"

echo ""
echo "=========================================="
echo "📊 VALIDATION SUMMARY"
echo "=========================================="
echo ""
echo -e "Tests Passed:  ${GREEN}$PASSED${NC}"
echo -e "Tests Failed:  ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validations passed!${NC}"
    echo ""
    echo "🎉 GW2Optimizer v1.1.0 is ready!"
    echo ""
    echo "Next steps:"
    echo "  1. Run the backend: cd backend && uvicorn app.main:app --reload"
    echo "  2. Test the API: curl http://localhost:8000/api/v1/meta/gw2-api/professions"
    echo "  3. Read the docs: docs/META_ANALYSIS.md"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some validations failed!${NC}"
    echo ""
    echo "Please fix the issues and run this script again."
    echo ""
    exit 1
fi
