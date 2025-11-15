#!/bin/bash
# Script to start a coverage testing session
# Usage: ./scripts/start-coverage-session.sh [session-number]

set -e

SESSION=${1:-1}
BRANCH="feature/coverage-session-${SESSION}"

echo "🎯 Starting Coverage Session ${SESSION}"
echo "================================"

# Check if Redis is running
echo "📡 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis not running. Starting Redis..."
    if command -v docker &> /dev/null; then
        docker run -d -p 6379:6379 --name gw2-redis redis:alpine
        echo "✅ Redis started in Docker"
    else
        echo "⚠️  Docker not found. Please start Redis manually:"
        echo "   docker run -d -p 6379:6379 redis:alpine"
        exit 1
    fi
else
    echo "✅ Redis is running"
fi

# Create branch
echo ""
echo "🌿 Creating branch: ${BRANCH}"
git checkout -b "${BRANCH}" 2>/dev/null || git checkout "${BRANCH}"

# Show coverage roadmap
echo ""
echo "📋 Coverage Roadmap for Session ${SESSION}:"
case ${SESSION} in
    1)
        echo "  - Auth & User Services"
        echo "  - Target: +8% coverage"
        echo "  - Files: app/api/auth.py, app/services/user_service.py, app/core/security.py"
        ;;
    2)
        echo "  - Builds API & Services"
        echo "  - Target: +10% coverage"
        echo "  - Files: app/api/builds.py, app/services/build_service_db.py"
        ;;
    3)
        echo "  - Teams API & Services"
        echo "  - Target: +8% coverage"
        echo "  - Files: app/api/teams.py, app/services/team_service_db.py"
        ;;
    4)
        echo "  - Critical Paths & Edge Cases"
        echo "  - Target: +5% coverage"
        echo "  - Files: Various middleware, error handlers, external clients"
        ;;
    *)
        echo "  - Custom session"
        ;;
esac

echo ""
echo "📖 See COVERAGE_ROADMAP.md for detailed plan"
echo ""
echo "🚀 Ready to start! Next steps:"
echo "   1. Write tests in backend/tests/"
echo "   2. Run: cd backend && poetry run pytest tests/test_XXX -v"
echo "   3. Check coverage: poetry run coverage report"
echo "   4. Commit: git add tests/ && git commit -m 'test: Session ${SESSION} coverage'"
echo ""
