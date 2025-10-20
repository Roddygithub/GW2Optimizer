#!/bin/bash
# Run all tests

echo "🧪 Running GW2Optimizer Tests..."

# Backend tests
echo "📋 Backend Tests..."
cd backend
source venv/bin/activate
pytest -v --cov=app --cov-report=term --cov-report=html
cd ..

echo "✅ All tests completed!"
