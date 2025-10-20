#!/bin/bash
# Start GW2Optimizer Backend

echo "🚀 Starting GW2Optimizer Backend..."

cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Start backend
echo "✅ Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
