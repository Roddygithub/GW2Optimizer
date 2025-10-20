#!/bin/bash
# Setup GW2Optimizer project

echo "🔧 Setting up GW2Optimizer..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required"; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo "⚠️  Ollama not found. Install from https://ollama.ai"; }

# Backend setup
echo "📦 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend
npm install
cd ..

# Create .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✏️  Please edit .env with your configuration"
fi

# Create data directories
mkdir -p backend/data/local_db
mkdir -p backend/data/training_data
mkdir -p backend/logs

# Make scripts executable
chmod +x scripts/*.sh

echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Start Ollama: ollama serve"
echo "3. Pull Mistral model: ollama pull mistral"
echo "4. Start backend: ./scripts/start-backend.sh"
echo "5. Start frontend: ./scripts/start-frontend.sh"
