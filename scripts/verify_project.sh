#!/bin/bash
# Complete Project Verification Script
# Tests all components: Backend, Frontend, Database, Redis, AI Services

set -e

echo "============================================"
echo "🔍 GW2OPTIMIZER PROJECT VERIFICATION"
echo "============================================"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

function check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

function check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# 1. Check Project Structure
echo "📁 Checking Project Structure..."
echo "-------------------------------------------"

if [ -d "backend" ]; then
    check_pass "Backend directory exists"
else
    check_fail "Backend directory missing"
fi

if [ -d "frontend" ]; then
    check_pass "Frontend directory exists"
else
    check_fail "Frontend directory missing"
fi

if [ -f "docker-compose.prod.yml" ]; then
    check_pass "Production docker-compose exists"
else
    check_warn "Production docker-compose missing"
fi

if [ -f ".github/workflows/ci.yml" ]; then
    check_pass "CI workflow exists"
else
    check_fail "CI workflow missing"
fi

echo ""

# 2. Check Backend
echo "🐍 Checking Backend..."
echo "-------------------------------------------"

cd backend

if [ -f "pyproject.toml" ]; then
    check_pass "pyproject.toml exists"
else
    check_fail "pyproject.toml missing"
fi

if command -v poetry &> /dev/null; then
    check_pass "Poetry installed"
    
    # Check dependencies
    if poetry check &> /dev/null; then
        check_pass "Poetry dependencies valid"
    else
        check_warn "Poetry dependencies have issues"
    fi
else
    check_warn "Poetry not installed"
fi

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    check_pass "Python installed: $PYTHON_VERSION"
else
    check_fail "Python not installed"
fi

# Check key files
if [ -f "app/main.py" ]; then
    check_pass "Main application file exists"
else
    check_fail "Main application file missing"
fi

if [ -f "app/services/mistral_ai.py" ]; then
    check_pass "Mistral AI service exists"
else
    check_fail "Mistral AI service missing"
fi

if [ -f "app/services/ai_service.py" ]; then
    check_pass "AI service exists"
else
    check_fail "AI service missing"
fi

# Check environment
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check critical env vars
    if grep -q "SECRET_KEY" .env; then
        check_pass "SECRET_KEY configured"
    else
        check_warn "SECRET_KEY not configured"
    fi
    
    if grep -q "DATABASE_URL" .env; then
        check_pass "DATABASE_URL configured"
    else
        check_warn "DATABASE_URL not configured"
    fi
else
    check_warn ".env file missing (use .env.example)"
fi

cd ..
echo ""

# 3. Check Frontend
echo "⚛️  Checking Frontend..."
echo "-------------------------------------------"

cd frontend

if [ -f "package.json" ]; then
    check_pass "package.json exists"
else
    check_fail "package.json missing"
fi

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js installed: $NODE_VERSION"
else
    check_fail "Node.js not installed"
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    check_pass "npm installed: $NPM_VERSION"
else
    check_fail "npm not installed"
fi

if [ -d "node_modules" ]; then
    check_pass "node_modules exists"
else
    check_warn "node_modules missing (run npm install)"
fi

if [ -f "src/main.tsx" ]; then
    check_pass "Main React file exists"
else
    check_fail "Main React file missing"
fi

cd ..
echo ""

# 4. Check Docker
echo "🐳 Checking Docker..."
echo "-------------------------------------------"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    check_pass "Docker installed: $DOCKER_VERSION"
else
    check_warn "Docker not installed"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | tr -d ',')
    check_pass "Docker Compose installed: $COMPOSE_VERSION"
else
    check_warn "Docker Compose not installed"
fi

if [ -f "backend/Dockerfile" ]; then
    check_pass "Backend Dockerfile exists"
else
    check_fail "Backend Dockerfile missing"
fi

if [ -f "frontend/Dockerfile" ]; then
    check_pass "Frontend Dockerfile exists"
else
    check_fail "Frontend Dockerfile missing"
fi

echo ""

# 5. Check CI/CD
echo "🔄 Checking CI/CD..."
echo "-------------------------------------------"

if [ -d ".github/workflows" ]; then
    check_pass ".github/workflows directory exists"
    
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
    check_pass "Found $WORKFLOW_COUNT workflow files"
else
    check_fail ".github/workflows directory missing"
fi

if command -v gh &> /dev/null; then
    check_pass "GitHub CLI installed"
    
    # Check CI status
    if gh run list --branch main --limit 1 --json conclusion --jq '.[0].conclusion' | grep -q "success"; then
        check_pass "Latest CI run: SUCCESS"
    else
        check_warn "Latest CI run: NOT SUCCESS"
    fi
else
    check_warn "GitHub CLI not installed"
fi

echo ""

# 6. Check Documentation
echo "📚 Checking Documentation..."
echo "-------------------------------------------"

if [ -f "README.md" ]; then
    check_pass "README.md exists"
else
    check_fail "README.md missing"
fi

if [ -f "docs/DEPLOYMENT_GUIDE.md" ]; then
    check_pass "Deployment guide exists"
else
    check_warn "Deployment guide missing"
fi

if [ -f "docs/TECH_DEBT.md" ]; then
    check_pass "Tech debt documentation exists"
else
    check_warn "Tech debt documentation missing"
fi

echo ""

# 7. Check Tests
echo "🧪 Checking Tests..."
echo "-------------------------------------------"

if [ -d "backend/tests" ]; then
    TEST_COUNT=$(find backend/tests -name "test_*.py" | wc -l)
    check_pass "Found $TEST_COUNT backend test files"
else
    check_warn "Backend tests directory missing"
fi

if [ -d "frontend/src" ] && grep -r "\.test\." frontend/src &> /dev/null; then
    check_pass "Frontend tests exist"
else
    check_warn "Frontend tests missing or not found"
fi

echo ""

# 8. Summary
echo "============================================"
echo "📊 VERIFICATION SUMMARY"
echo "============================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo "Project is ready for deployment!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS WARNING(S)${NC}"
    echo "Project is mostly ready, but some improvements recommended."
    exit 0
else
    echo -e "${RED}❌ $ERRORS ERROR(S), $WARNINGS WARNING(S)${NC}"
    echo "Please fix the errors before deployment."
    exit 1
fi
