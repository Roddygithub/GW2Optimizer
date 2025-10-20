#!/bin/bash
# Start GW2Optimizer Frontend

echo "🚀 Starting GW2Optimizer Frontend..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start frontend
echo "✅ Starting Vite dev server..."
npm run dev
