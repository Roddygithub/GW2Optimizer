#!/bin/bash

# Script de test des endpoints API GW2Optimizer v4.1.0
# =====================================================

API_URL="http://localhost:8000/api/v1"
RESULTS_FILE="/tmp/api_test_results.txt"

# Utilisateur de test unique par exécution
TIMESTAMP=$(date +%s)
TEST_EMAIL="api_${TIMESTAMP}@example.com"
TEST_USERNAME="test_api_user_${TIMESTAMP}"
TEST_PASSWORD="TestPass123!"

echo "🧪 Tests des endpoints API GW2Optimizer v4.1.0" > $RESULTS_FILE
echo "================================================" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# Fonction de test
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local auth=$5
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        if [ -n "$auth" ]; then
            response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $auth" "$API_URL$endpoint")
        else
            response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
        fi
    else
        if [ -n "$auth" ]; then
            response=$(curl -s -w "\n%{http_code}" -X $method -H "Content-Type: application/json" -H "Authorization: Bearer $auth" -d "$data" "$API_URL$endpoint")
        else
            response=$(curl -s -w "\n%{http_code}" -X $method -H "Content-Type: application/json" -d "$data" "$API_URL$endpoint")
        fi
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo "✅ PASS ($http_code)"
        echo "✅ $name - PASS ($http_code)" >> $RESULTS_FILE
    elif [ "$http_code" -eq 404 ]; then
        echo "❌ FAIL ($http_code - Not Found)"
        echo "❌ $name - FAIL ($http_code - Not Found)" >> $RESULTS_FILE
    elif [ "$http_code" -eq 401 ]; then
        echo "⚠️  AUTH ($http_code - Unauthorized)"
        echo "⚠️  $name - AUTH ($http_code - Unauthorized)" >> $RESULTS_FILE
    else
        echo "❌ FAIL ($http_code)"
        echo "❌ $name - FAIL ($http_code)" >> $RESULTS_FILE
    fi
    
    echo "   Response: ${body:0:100}..." >> $RESULTS_FILE
    echo "" >> $RESULTS_FILE
}

# 0. Préparation de l'utilisateur de test
echo "🔐 0. Préparation de l'utilisateur de test ($TEST_EMAIL)"
REGISTER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"username\":\"$TEST_USERNAME\",\"password\":\"$TEST_PASSWORD\"}")

if [ "$REGISTER_STATUS" = "201" ]; then
    echo "✅ Utilisateur de test créé" | tee -a $RESULTS_FILE
else
    echo "❌ Échec de préparation de l'utilisateur de test (status: $REGISTER_STATUS)" | tee -a $RESULTS_FILE
    exit 1
fi

# 1. Test Health
echo "📊 1. Tests de santé"
test_endpoint "Health Check" "GET" "/health" "" ""

# 2. Test Auth
echo ""
echo "🔐 2. Tests d'authentification"
TOKEN=$(curl -s -X POST "$API_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL&password=$TEST_PASSWORD" \
  | grep -o '"access_token":"[^\"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "✅ Token obtenu"
    echo "✅ Token obtenu: ${TOKEN:0:50}..." >> $RESULTS_FILE
else
    echo "❌ Échec d'obtention du token"
    echo "❌ Échec d'obtention du token" >> $RESULTS_FILE
    exit 1
fi

# 3. Test Builds
echo ""
echo "🏗️  3. Tests des Builds"
test_endpoint "List Builds" "GET" "/builds?limit=10" "" "$TOKEN"
test_endpoint "Create Build" "POST" "/builds" '{"name":"Test Build","profession":"Guardian","game_mode":"zerg","role":"support","description":"Test build for validation","is_public":false}' "$TOKEN"

# 4. Test Teams
echo ""
echo "👥 4. Tests des Teams"
test_endpoint "List Teams" "GET" "/teams?limit=5" "" "$TOKEN"
test_endpoint "Create Team" "POST" "/teams" '{"name":"Test Team","game_mode":"zerg","team_size":5,"description":"Test team composition","is_public":false,"build_ids":[]}' "$TOKEN"

# 5. Test AI Endpoints (sans auth pour certains)
echo ""
echo "🤖 5. Tests des endpoints AI"
test_endpoint "AI Context" "GET" "/ai/context" "" ""

# AI Compose nécessite l'auth
test_endpoint "AI Compose" "POST" "/ai/compose" '{"game_mode":"raid","team_size":5,"preferences":{"roles":["heal","dps","dps","dps","dps"]}}' "$TOKEN"

# AI Feedback
test_endpoint "AI Feedback" "POST" "/ai/feedback" '{"target_id":"test-123","rating":8,"comment":"Good composition"}' "$TOKEN"

# 6. Résumé
echo ""
echo "📋 Résumé des tests"
echo "==================="
passed=$(grep -c "✅.*PASS" $RESULTS_FILE)
failed=$(grep -c "❌.*FAIL" $RESULTS_FILE)
auth_issues=$(grep -c "⚠️.*AUTH" $RESULTS_FILE)
total=$((passed + failed + auth_issues))

echo "Total: $total tests"
echo "✅ Réussis: $passed"
echo "❌ Échoués: $failed"
echo "⚠️  Auth requis: $auth_issues"

echo "" >> $RESULTS_FILE
echo "📊 RÉSUMÉ" >> $RESULTS_FILE
echo "=========" >> $RESULTS_FILE
echo "Total: $total tests" >> $RESULTS_FILE
echo "✅ Réussis: $passed" >> $RESULTS_FILE
echo "❌ Échoués: $failed" >> $RESULTS_FILE
echo "⚠️  Auth requis: $auth_issues" >> $RESULTS_FILE

echo ""
echo "📄 Rapport complet: $RESULTS_FILE"
cat $RESULTS_FILE
