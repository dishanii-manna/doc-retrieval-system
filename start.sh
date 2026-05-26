#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$ROOT_DIR/docker"

if docker compose version &>/dev/null; then
  COMPOSE="docker compose"
else
  COMPOSE="docker-compose"
fi

echo "🚀 Starting BookSearch Document Retrieval System..."
echo ""

# Docker Compose requires backend/.env (see README)
if [ ! -f "$ROOT_DIR/backend/.env" ]; then
  if [ -f "$ROOT_DIR/backend/.env.example" ]; then
    cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
    echo "📋 Created backend/.env from .env.example"
  else
    echo "❌ Missing backend/.env — copy backend/.env.example to backend/.env"
    exit 1
  fi
fi

cd "$DOCKER_DIR"

echo "📦 Step 1 — Building and starting containers..."
$COMPOSE up -d --build

echo ""
echo "⏳ Step 2 — Waiting for Elasticsearch..."

for _ in $(seq 1 60); do
  if docker inspect --format='{{.State.Health.Status}}' es_books 2>/dev/null | grep -q "healthy"; then
    echo "✅ Elasticsearch is ready"
    break
  fi
  sleep 2
done

if ! docker inspect --format='{{.State.Health.Status}}' es_books 2>/dev/null | grep -q "healthy"; then
  echo "❌ Elasticsearch failed"
  docker logs es_books
  exit 1
fi

echo ""
echo "⏳ Step 3 — Waiting for backend..."

for _ in $(seq 1 40); do
  if docker inspect --format='{{.State.Health.Status}}' backend_books 2>/dev/null | grep -q "healthy"; then
    echo "✅ Backend is ready"
    break
  fi
  sleep 2
done

if ! docker inspect --format='{{.State.Health.Status}}' backend_books 2>/dev/null | grep -q "healthy"; then
  echo "❌ Backend failed"
  docker logs backend_books
  exit 1
fi

echo ""
echo "📖 Step 4 — Indexing books..."

docker exec backend_books python -m ingestion.pipeline \
  --ocr-dir /data/ocr \
  --metadata /data/metadata/books.csv \
  --reset

echo ""
echo "✅ System is ready!"
echo "👉 Open: http://127.0.0.1:3000"
echo ""
echo "To stop: $COMPOSE down"
