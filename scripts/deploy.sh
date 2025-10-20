#!/bin/bash
# Deploy GW2Optimizer to production

echo "🚀 Deploying GW2Optimizer..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm run build
cd ..

# Run tests
echo "🧪 Running tests..."
cd backend
source venv/bin/activate
pytest
cd ..

# Deploy (placeholder - configure with your deployment target)
echo "📤 Deploying to production..."
echo "✅ Deployment completed!"
echo "🌐 Application available at: https://gw2optimizer.windsurf.app"
