#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Démarrage environnement de développement..."

COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    echo "✅ Docker Compose v2 détecté"
    COMPOSE_CMD="docker compose -f docker-compose.dev.yml"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "✅ Docker Compose v1 détecté"
    COMPOSE_CMD="docker-compose -f docker-compose.dev.yml"
  else
    echo "⚠️  Docker trouvé mais Compose manquant"
  fi
else
  echo "⚠️  Docker non installé"
fi

if [ -n "$COMPOSE_CMD" ]; then
  $COMPOSE_CMD up -d
  echo "⏳ Attente Postgres..."
  timeout 30 bash -c "until $COMPOSE_CMD exec -T postgres pg_isready -U dev -d gw2optimizer; do sleep 1; done" || true
  echo "⏳ Attente Redis..."
  timeout 30 bash -c "until $COMPOSE_CMD exec -T redis redis-cli ping; do sleep 1; done" || true
  echo "✅ Services Docker prêts (ou en cours de démarrage)."
else
  echo "📝 Mode SQLite activé (tests unitaires OK)"
  export DATABASE_URL="sqlite+aiosqlite:///./gw2optimizer.db"
  export REDIS_ENABLED=false
fi

echo "✅ Environnement prêt !"
