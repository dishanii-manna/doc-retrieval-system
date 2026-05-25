#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOCKER_DIR="$ROOT_DIR/docker"

# Prefer Docker Compose V2 plugin; fall back to docker-compose.
if docker compose version &>/dev/null; then
  COMPOSE="docker compose"
else
  COMPOSE="docker-compose"
fi

echo "🚀 Starting BookSearch Document Retrieval System..."
echo ""

cd "$DOCKER_DIR"

# Rebuild images so backend/frontend code changes are included (only ../data is mounted at runtime).
echo "📦 Step 1 — Building and starting containers..."
$COMPOSE up -d --build

echo ""
echo "⏳ Step 2 — Waiting for Elasticsearch..."
for _ in $(seq 1 45); do
  if curl -sf http://127.0.0.1:9200/_cluster/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! curl -sf http://127.0.0.1:9200/_cluster/health >/dev/null 2>&1; then
  echo "❌ Elasticsearch did not become ready. Check: docker logs es_books"
  exit 1
fi

echo "⏳ Waiting for backend..."
for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "❌ Backend did not become ready. Check: docker logs backend_books"
  exit 1
fi

echo ""
echo "📖 Step 3 — Indexing books into Elasticsearch (applies latest ocr_parser / ingestion code)..."
docker exec backend_books python -m ingestion.pipeline \
  --ocr-dir /data/ocr \
  --metadata /data/metadata/books.csv \
  --reset

echo ""
echo "✅ System is ready!"
echo "👉 Open your browser: http://127.0.0.1:3000"
echo ""
echo "To stop later, from the docker folder run: $COMPOSE down"