#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_URL="http://localhost:8000"
TEST_REPORT="test_report.txt"
PASSWORD="TestPass1234!"
TESTS_PASSED=0
TESTS_FAILED=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$TEST_REPORT"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$TEST_REPORT"; TESTS_PASSED=$((TESTS_PASSED + 1)); }
log_error() { echo -e "${RED}[✗]${NC} $1" | tee -a "$TEST_REPORT"; TESTS_FAILED=$((TESTS_FAILED + 1)); }

cat > "$TEST_REPORT" << EOF
# GW2Optimizer - Real Conditions E2E Test Report
Date: $(date '+%Y-%m-%d %H:%M:%S')
Environment: ${ENVIRONMENT:-production}
EOF

log_info "🚀 Starting E2E Tests"

# Test 1: Backend Health
if curl -sf "$BACKEND_URL/health" > /dev/null; then
    log_success "Backend health check"
else
    log_error "Backend health check"
fi

# Test 2: User Registration
TIMESTAMP=$(date +%s)
REGISTER=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"e2e$TIMESTAMP@test.com\",\"username\":\"e2e$TIMESTAMP\",\"password\":\"$PASSWORD\"}")

if echo "$REGISTER" | grep -q '"id"'; then
    log_success "User registration"
    EMAIL=$(echo "$REGISTER" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
else
    log_error "User registration"
fi

# Test 3: User Login
if [ ! -z "$EMAIL" ]; then
    LOGIN=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$EMAIL&password=$PASSWORD")
    
    if echo "$LOGIN" | grep -q '"access_token"'; then
        log_success "User login"
        TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    else
        log_error "User login"
    fi
fi

# Test 4: Protected Endpoint
if [ ! -z "$TOKEN" ]; then
    PROFILE=$(curl -s -H "Authorization: Bearer $TOKEN" "$BACKEND_URL/api/v1/auth/me")
    if echo "$PROFILE" | grep -q '"email"'; then
        log_success "Protected endpoint access"
    else
        log_error "Protected endpoint access"
    fi
fi

# Test 5: Build Creation
if [ ! -z "$TOKEN" ]; then
    BUILD=$(curl -s -X POST "$BACKEND_URL/api/v1/builds" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name":"E2E Test Build",
            "profession":"Guardian",
            "game_mode":"wvw",
            "role":"support",
            "is_public":false,
            "trait_lines":[],
            "skills":[],
            "equipment":[]
        }')
    
    if echo "$BUILD" | grep -q '"id"'; then
        log_success "Build creation"
    else
        log_error "Build creation"
    fi
fi

# Test 6: GW2 API (if key available)
if [ ! -z "$GW2_API_KEY" ]; then
    GW2_RESPONSE=$(curl -s "https://api.guildwars2.com/v2/account" \
        -H "Authorization: Bearer $GW2_API_KEY")
    
    if echo "$GW2_RESPONSE" | grep -q '"name"'; then
        log_success "GW2 API integration"
    else
        log_error "GW2 API integration"
    fi
else
    log_info "Skipping GW2 API test (no key)"
fi

# Test 7: Mistral AI (if key available)
if [ ! -z "$MISTRAL_API_KEY" ]; then
    MISTRAL_RESPONSE=$(curl -s -X POST "https://api.mistral.ai/v1/chat/completions" \
        -H "Authorization: Bearer $MISTRAL_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "model":"mistral-small-latest",
            "messages":[{"role":"user","content":"Generate a GW2 build name for Guardian support"}],
            "max_tokens":50
        }')
    
    if echo "$MISTRAL_RESPONSE" | grep -q '"content"'; then
        log_success "Mistral AI integration"
        echo "$MISTRAL_RESPONSE" > response.json
    else
        log_error "Mistral AI integration"
    fi
else
    log_info "Skipping Mistral AI test (no key)"
fi

# Summary
echo "" | tee -a "$TEST_REPORT"
echo "================================================" | tee -a "$TEST_REPORT"
echo "SUMMARY" | tee -a "$TEST_REPORT"
echo "================================================" | tee -a "$TEST_REPORT"
echo "Tests Passed: $TESTS_PASSED" | tee -a "$TEST_REPORT"
echo "Tests Failed: $TESTS_FAILED" | tee -a "$TEST_REPORT"
echo "================================================" | tee -a "$TEST_REPORT"

if [ $TESTS_FAILED -gt 0 ]; then
    log_error "Some tests failed"
    exit 1
else
    log_success "All tests passed!"
    exit 0
fi
