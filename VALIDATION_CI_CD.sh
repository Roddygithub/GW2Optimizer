#!/bin/bash

# 🚀 GW2Optimizer - CI/CD Validation Script
# Validates all critical components before deployment

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  GW2Optimizer v1.3.0 - CI/CD Validation                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        FAILED=1
    fi
}

echo -e "${BLUE}1️⃣ Backend Tests${NC}"
cd backend
pytest tests/test_meta_agent.py tests/test_gw2_api_client.py tests/test_meta_analysis_workflow.py -v --tb=short > /tmp/test_results.txt 2>&1
TEST_RESULT=$?
print_status $TEST_RESULT "Backend core tests (Meta Agent, GW2 API, Workflow)"

if [ $TEST_RESULT -eq 0 ]; then
    PASSED=$(grep -c "passed" /tmp/test_results.txt || echo "0")
    echo -e "   ${GREEN}$PASSED tests passed${NC}"
fi

echo ""
echo -e "${BLUE}2️⃣ Code Quality${NC}"
python -m ruff check app/ --select E,F,W --quiet > /dev/null 2>&1
RUFF_RESULT=$?
print_status $RUFF_RESULT "Ruff linting (E, F, W rules)"

echo ""
echo -e "${BLUE}3️⃣ Coverage Check${NC}"
pytest tests/test_meta_agent.py tests/test_gw2_api_client.py tests/test_meta_analysis_workflow.py --cov=app/agents --cov=app/services/gw2_api_client --cov=app/workflows/meta_analysis_workflow --cov-report=term-missing -q > /tmp/coverage.txt 2>&1
COVERAGE_RESULT=$?

if [ $COVERAGE_RESULT -eq 0 ]; then
    # Extract coverage percentage
    COVERAGE=$(grep "TOTAL" /tmp/coverage.txt | awk '{print $4}' | sed 's/%//')
    if [ ! -z "$COVERAGE" ]; then
        if (( $(echo "$COVERAGE >= 50" | bc -l) )); then
            echo -e "${GREEN}✅ Coverage: ${COVERAGE}%${NC}"
        else
            echo -e "${YELLOW}⚠️  Coverage: ${COVERAGE}% (target: 80%)${NC}"
        fi
    fi
else
    print_status 1 "Coverage check"
fi

cd ..

echo ""
echo -e "${BLUE}4️⃣ Project Structure${NC}"
[ -f "README.md" ] && print_status 0 "README.md exists" || print_status 1 "README.md missing"
[ -f "CHANGELOG.md" ] && print_status 0 "CHANGELOG.md exists" || print_status 1 "CHANGELOG.md missing"
[ -f "LICENSE" ] && print_status 0 "LICENSE exists" || print_status 1 "LICENSE missing"

echo ""
echo -e "${BLUE}5️⃣ Documentation${NC}"
[ -f "DOC_INDEX.md" ] && print_status 0 "DOC_INDEX.md exists" || print_status 1 "DOC_INDEX.md missing"
[ -f "PROJECT_STRUCTURE.md" ] && print_status 0 "PROJECT_STRUCTURE.md exists" || print_status 1 "PROJECT_STRUCTURE.md missing"
[ -d "docs" ] && print_status 0 "docs/ directory exists" || print_status 1 "docs/ directory missing"

echo ""
echo "════════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ CI/CD Validation PASSED${NC}"
    exit 0
else
    echo -e "${RED}❌ CI/CD Validation FAILED${NC}"
    exit 1
fi
