#!/usr/bin/env bash
# Start GW2Optimizer Backend (Poetry-based)

set -euo pipefail

echo "🚀 Starting GW2Optimizer Backend..."

# Se placer dans le dossier backend à partir du chemin du script, peu importe le CWD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../backend"

# Ensure Poetry is available
if ! command -v poetry >/dev/null 2>&1; then
    echo "❌ Poetry n'est pas installé. Installe-le puis relance ce script."
    exit 1
fi

echo "📥 Installing backend dependencies with Poetry..."
poetry install

# Create logs directory (used by uvicorn logging if configured)
mkdir -p logs

# Ensure Ollama is running (optional, for local AI features)
if command -v ollama >/dev/null 2>&1; then
    OLLAMA_URL="${OLLAMA_HOST:-http://localhost:11434}"
    if ! curl -sSf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
        echo "🧠 Starting Ollama server..."
        nohup ollama serve > logs/ollama.log 2>&1 &
        sleep 3
    fi
else
    echo "⚠️ Ollama n'est pas installé. Les fonctionnalités IA locales peuvent ne pas fonctionner."
fi

echo "✅ Starting FastAPI server with Poetry..."
exec poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
