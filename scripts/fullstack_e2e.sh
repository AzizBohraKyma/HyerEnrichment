#!/usr/bin/env bash
# Full-stack integration E2E: start backend Compose stack, poll health, run Playwright integration tests.
#
# Usage (from repo root):
#   bash scripts/fullstack_e2e.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_DIR="$REPO_ROOT/backend/docker"
BASE="${BACKEND_API_URL:-http://localhost:8000}"
BASE="${BASE%/}"

echo "== bringing up api, worker, redis, postgres =="
cd "$COMPOSE_DIR"
docker compose up --build -d api worker redis postgres

echo "== waiting for API health =="
ready=0
for _ in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/health" || true)"
  if [ "$code" = "200" ]; then
    ready=1
    break
  fi
  sleep 2
done

if [ "$ready" -ne 1 ]; then
  echo "FAIL  health never returned 200 at $BASE/health" >&2
  exit 1
fi

echo "PASS  health 200"

echo "== running Playwright integration tests =="
cd "$REPO_ROOT/frontend"
npm run test:integration
