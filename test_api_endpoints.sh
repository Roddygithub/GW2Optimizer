#!/bin/bash

# Script de test pour les endpoints API de GW2Optimizer
# Génère un rapport au format Markdown

REPORT_FILE="../STAGING_VALIDATION_REPORT.md"
API_BASE="http://localhost:8001/api/v1"

# Fonction pour formater le résultat des tests
format_test_result() {
    local status=$1
    local message=$2
    
    if [ "$status" -eq 0 ]; then
        echo "✅ $message"
    else
        echo "❌ $message"
    fi
}

# En-tête du rapport
cat > "$REPORT_FILE" << EOL
# Rapport de Validation - GW2Optimizer v4.1.0

## 🚀 Tests des Endpoints API

### 1. Test d'authentification

EOL

# Test d'authentification
echo "🔐 Test d'authentification..."
AUTH_RESPONSE=$(curl -s -X POST "$API_BASE/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=Test123!")

if [ $? -eq 0 ] && echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    echo "✅ Authentification réussie" | tee -a "$REPORT_FILE"
    ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
    
    # Ajout des en-têtes d'autorisation pour les requêtes suivantes
    AUTH_HEADER="Authorization: Bearer $ACCESS_TOKEN"
    
    # Test des endpoints protégés
    echo -e "\n### 2. Endpoints Protégés\n" | tee -a "$REPORT_FILE"
    
    # Test de l'endpoint de santé
    echo "🩺 Test de l'endpoint de santé..."
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/health")
    if [ "$HEALTH_RESPONSE" -eq 200 ]; then
        echo "✅ Health check réussi ($HEALTH_RESPONSE)" | tee -a "$REPORT_FILE"
    else
        echo "❌ Health check échoué ($HEALTH_RESPONSE)" | tee -a "$REPORT_FILE"
    fi
    
    # Test de l'endpoint de contexte IA
    echo "🧠 Test de l'endpoint de contexte IA..."
    CONTEXT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$API_BASE/ai/context")
    if [ "$CONTEXT_RESPONSE" -eq 200 ]; then
        echo "✅ Récupération du contexte IA réussie ($CONTEXT_RESPONSE)" | tee -a "$REPORT_FILE"
    else
        echo "⚠️  Échec de la récupération du contexte IA ($CONTEXT_RESPONSE) - Vérifiez la configuration de l'IA" | tee -a "$REPORT_FILE"
    fi
    
    # Test de l'endpoint de composition d'équipe
    echo "🎮 Test de l'endpoint de composition d'équipe..."
    COMPOSE_PAYLOAD='{"game_mode": "raid", "team_size": 5, "preferences": {}}'
    COMPOSE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_BASE/ai/compose" \
        -H "$AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d "$COMPOSE_PAYLOAD")
        
    if [ "$COMPOSE_RESPONSE" -eq 200 ] || [ "$COMPOSE_RESPONSE" -eq 202 ]; then
        echo "✅ Composition d'équipe réussie ($COMPOSE_RESPONSE)" | tee -a "$REPORT_FILE"
    else
        echo "⚠️  Échec de la composition d'équipe ($COMPOSE_RESPONSE) - Vérifiez la configuration de l'IA" | tee -a "$REPORT_FILE"
    fi
    
    # Test de l'endpoint de feedback
    echo "📝 Test de l'endpoint de feedback..."
    FEEDBACK_PAYLOAD='{"feedback_type": "rating", "rating": 5, "comments": "Test automatisé"}'
    FEEDBACK_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$API_BASE/ai/feedback" \
        -H "$AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d "$FEEDBACK_PAYLOAD")
        
    if [ "$FEEDBACK_RESPONSE" -eq 200 ] || [ "$FEEDBACK_RESPONSE" -eq 201 ]; then
        echo "✅ Soumission de feedback réussie ($FEEDBACK_RESPONSE)" | tee -a "$REPORT_FILE"
    else
        echo "⚠️  Échec de la soumission de feedback ($FEEDBACK_RESPONSE) - Vérifiez la configuration de la base de données" | tee -a "$REPORT_FILE"
    fi
    
    # Test des endpoints de builds
    echo -e "\n### 3. Gestion des Builds\n" | tee -a "$REPORT_FILE"
    
    # Récupération des builds
    echo "📋 Test de récupération des builds..."
    BUILDS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$API_BASE/builds")
    if [ "$BUILDS_RESPONSE" -eq 200 ]; then
        echo "✅ Récupération des builds réussie ($BUILDS_RESPONSE)" | tee -a "$REPORT_FILE"
    else
        echo "⚠️  Échec de la récupération des builds ($BUILDS_RESPONSE) - Vérifiez la configuration de la base de données" | tee -a "$REPORT_FILE"
    fi
    
else
    echo "❌ Échec de l'authentification" | tee -a "$REPORT_FILE"
    echo "Réponse du serveur: $AUTH_RESPONSE" | tee -a "$REPORT_FILE"
fi

# Ajout des informations système
echo -e "\n## 🖥️ Informations Système\n" | tee -a "$REPORT_FILE"
echo "- Date du test: $(date)" | tee -a "$REPORT_FILE"
echo "- Version de l'API: 1.0.0" | tee -a "$REPORT_FILE"
echo "- URL de base: $API_BASE" | tee -a "$REPORT_FILE"

echo -e "\n## 📊 Résumé des Tests" | tee -a "$REPORT_FILE"

# Comptage des tests réussis/échoués
SUCCESS_COUNT=$(grep -c "✅" "$REPORT_FILE")
WARNING_COUNT=$(grep -c "⚠️" "$REPORT_FILE")
ERROR_COUNT=$(grep -c "❌" "$REPORT_FILE")

echo -e "\n- Tests réussis: $SUCCESS_COUNT" | tee -a "$REPORT_FILE"
echo -e "- Avertissements: $WARNING_COUNT" | tee -a "$REPORT_FILE"
echo -e "- Échecs: $ERROR_COUNT" | tee -a "$REPORT_FILE"

# Conclusion
if [ "$ERROR_COUNT" -eq 0 ]; then
    if [ "$WARNING_COUNT" -eq 0 ]; then
        echo -e "\n## 🎉 Tous les tests ont réussi !" | tee -a "$REPORT_FILE"
    else
        echo -e "\n## ⚠️  Tests terminés avec des avertissements" | tee -a "$REPORT_FILE"
    fi
else
    echo -e "\n## ❌ Des erreurs ont été détectées" | tee -a "$REPORT_FILE"
fi

echo -e "\n---\nRapport généré le $(date)" | tee -a "$REPORT_FILE"

echo -e "\n✅ Rapport de validation généré: $REPORT_FILE"
