#!/bin/bash

# Script de test des endpoints API pour GW2Optimizer v4.1.0
# Génère un rapport JSON avec les résultats

API_BASE="http://localhost:8001"
REPORT_FILE="../logs/api_test_results.json"

echo "🔍 Test des endpoints API GW2Optimizer v4.1.0"
echo "=============================================="
echo ""

# Initialiser le rapport JSON
echo "{" > "$REPORT_FILE"
echo '  "test_date": "'$(date -Iseconds)'",' >> "$REPORT_FILE"
echo '  "api_base": "'$API_BASE'",' >> "$REPORT_FILE"
echo '  "endpoints": {' >> "$REPORT_FILE"

# Test 1: Health Check
echo "📊 Test 1/5: GET /api/v1/health"
START=$(date +%s%N)
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE/api/v1/health")
END=$(date +%s%N)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
DURATION=$(( (END - START) / 1000000 ))

echo '    "health": {' >> "$REPORT_FILE"
echo '      "status_code": '$HTTP_CODE',' >> "$REPORT_FILE"
echo '      "response_time_ms": '$DURATION',' >> "$REPORT_FILE"
echo '      "response": '"$(echo "$BODY" | jq -c .)"'' >> "$REPORT_FILE"
echo '    },' >> "$REPORT_FILE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Status: 200 OK (${DURATION}ms)"
else
    echo "   ❌ Status: $HTTP_CODE (${DURATION}ms)"
fi
echo ""

# Test 2: Auth Token
echo "📊 Test 2/5: POST /api/v1/auth/token"
START=$(date +%s%N)
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123!" \
  --max-time 5)
END=$(date +%s%N)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)
DURATION=$(( (END - START) / 1000000 ))

echo '    "auth_token": {' >> "$REPORT_FILE"
echo '      "status_code": '$HTTP_CODE',' >> "$REPORT_FILE"
echo '      "response_time_ms": '$DURATION',' >> "$REPORT_FILE"
echo '      "response": '"$(echo "$BODY" | jq -c . 2>/dev/null || echo '"{}"')"'' >> "$REPORT_FILE"
echo '    },' >> "$REPORT_FILE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Status: 200 OK (${DURATION}ms)"
    TOKEN=$(echo "$BODY" | jq -r '.access_token' 2>/dev/null)
else
    echo "   ❌ Status: $HTTP_CODE (${DURATION}ms)"
    TOKEN=""
fi
echo ""

# Test 3: AI Context (nécessite authentification)
echo "📊 Test 3/5: GET /api/v1/ai/context"
if [ -n "$TOKEN" ]; then
    START=$(date +%s%N)
    RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE/api/v1/ai/context" \
      -H "Authorization: Bearer $TOKEN" \
      --max-time 5)
    END=$(date +%s%N)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    DURATION=$(( (END - START) / 1000000 ))
    
    echo '    "ai_context": {' >> "$REPORT_FILE"
    echo '      "status_code": '$HTTP_CODE',' >> "$REPORT_FILE"
    echo '      "response_time_ms": '$DURATION',' >> "$REPORT_FILE"
    echo '      "response": '"$(echo "$BODY" | jq -c . 2>/dev/null || echo '"{}"')"'' >> "$REPORT_FILE"
    echo '    },' >> "$REPORT_FILE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Status: 200 OK (${DURATION}ms)"
    else
        echo "   ❌ Status: $HTTP_CODE (${DURATION}ms)"
    fi
else
    echo '    "ai_context": {' >> "$REPORT_FILE"
    echo '      "status_code": 0,' >> "$REPORT_FILE"
    echo '      "response_time_ms": 0,' >> "$REPORT_FILE"
    echo '      "response": "Skipped - No auth token"' >> "$REPORT_FILE"
    echo '    },' >> "$REPORT_FILE"
    echo "   ⚠️  Skipped - No auth token"
fi
echo ""

# Test 4: AI Compose (nécessite authentification)
echo "📊 Test 4/5: POST /api/v1/ai/compose"
if [ -n "$TOKEN" ]; then
    START=$(date +%s%N)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/ai/compose" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"game_mode":"raid","requirements":"High DPS team for Wing 1"}' \
      --max-time 10)
    END=$(date +%s%N)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    DURATION=$(( (END - START) / 1000000 ))
    
    echo '    "ai_compose": {' >> "$REPORT_FILE"
    echo '      "status_code": '$HTTP_CODE',' >> "$REPORT_FILE"
    echo '      "response_time_ms": '$DURATION',' >> "$REPORT_FILE"
    echo '      "response": '"$(echo "$BODY" | jq -c . 2>/dev/null || echo '"{}"')"'' >> "$REPORT_FILE"
    echo '    },' >> "$REPORT_FILE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Status: 200 OK (${DURATION}ms)"
    else
        echo "   ❌ Status: $HTTP_CODE (${DURATION}ms)"
    fi
else
    echo '    "ai_compose": {' >> "$REPORT_FILE"
    echo '      "status_code": 0,' >> "$REPORT_FILE"
    echo '      "response_time_ms": 0,' >> "$REPORT_FILE"
    echo '      "response": "Skipped - No auth token"' >> "$REPORT_FILE"
    echo '    },' >> "$REPORT_FILE"
    echo "   ⚠️  Skipped - No auth token"
fi
echo ""

# Test 5: AI Feedback (nécessite authentification)
echo "📊 Test 5/5: POST /api/v1/ai/feedback"
if [ -n "$TOKEN" ]; then
    START=$(date +%s%N)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/api/v1/ai/feedback" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"composition_id":"test-123","rating":5,"comment":"Great composition!"}' \
      --max-time 5)
    END=$(date +%s%N)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    DURATION=$(( (END - START) / 1000000 ))
    
    echo '    "ai_feedback": {' >> "$REPORT_FILE"
    echo '      "status_code": '$HTTP_CODE',' >> "$REPORT_FILE"
    echo '      "response_time_ms": '$DURATION',' >> "$REPORT_FILE"
    echo '      "response": '"$(echo "$BODY" | jq -c . 2>/dev/null || echo '"{}"')"'' >> "$REPORT_FILE"
    echo '    }' >> "$REPORT_FILE"
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
        echo "   ✅ Status: $HTTP_CODE OK (${DURATION}ms)"
    else
        echo "   ❌ Status: $HTTP_CODE (${DURATION}ms)"
    fi
else
    echo '    "ai_feedback": {' >> "$REPORT_FILE"
    echo '      "status_code": 0,' >> "$REPORT_FILE"
    echo '      "response_time_ms": 0,' >> "$REPORT_FILE"
    echo '      "response": "Skipped - No auth token"' >> "$REPORT_FILE"
    echo '    }' >> "$REPORT_FILE"
    echo "   ⚠️  Skipped - No auth token"
fi
echo ""

# Fermer le rapport JSON
echo '  }' >> "$REPORT_FILE"
echo '}' >> "$REPORT_FILE"

echo "=============================================="
echo "✅ Tests terminés. Rapport sauvegardé dans: $REPORT_FILE"
