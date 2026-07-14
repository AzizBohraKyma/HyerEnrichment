#!/usr/bin/env bash
# CI-safe fake sidecar E2E: compose override + deterministic integration probe.
#
# Verifies:
#   1. Fake sidecar containers healthy
#   2. api/worker reach sidecars on Docker network
#   3. Sidecar enrichers return fixture data
#   4. Async tier4 job includes Google Maps Scraper business data
#
# Usage:
#   bash backend/scripts/e2e_fake_sidecars.sh
#
# Requires: docker + docker compose (WSL2/Linux recommended).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/../docker" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE="http://localhost:8000"
COMPOSE_FILES=(--profile paid -f docker-compose.yml -f docker-compose.fake-sidecars.yml)

cd "$COMPOSE_DIR"

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; exit 1; }

mkdir -p "$BACKEND_DIR/.e2e-results"

cleanup() {
  if [ "${E2E_KEEP_STACK:-0}" != "1" ]; then
    docker compose "${COMPOSE_FILES[@]}" down
  fi
}
trap cleanup EXIT

echo "== bringing up fake-sidecar stack =="
export ENABLE_TIER1=false
docker compose "${COMPOSE_FILES[@]}" up --build -d \
  api worker redis postgres social-analyzer google-maps-scraper email-verifier reacher

echo "== waiting for API health =="
for i in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/health" || true)"
  [ "$code" = "200" ] && break
  sleep 2
done
[ "$code" = "200" ] || fail "health never returned 200 (last=$code)"
pass "health 200"

echo "== worker reachability to sidecars =="
docker compose "${COMPOSE_FILES[@]}" exec -T worker sh -c '
  set -e
  python -c "import urllib.request; urllib.request.urlopen(\"http://social-analyzer:9005/health\")"
  python -c "import urllib.request; urllib.request.urlopen(\"http://google-maps-scraper:8080/health\")"
  python -c "import urllib.request; urllib.request.urlopen(\"http://email-verifier:8080/v1/health@example.com/verification\")"
  python -c "import urllib.request; urllib.request.urlopen(\"http://reacher:8080/health\")"
'
pass "worker can reach all fake sidecars"

echo "== fake sidecar probe inside api =="
docker compose "${COMPOSE_FILES[@]}" exec -T api sh -c '
  set -e
  export E2E_BASE_URL=http://127.0.0.1:8000
  export E2E_BACKEND_ROOT=/app/backend
  cd /app/backend
  mkdir -p /app/backend/.e2e-results
  python -
' < "$SCRIPT_DIR/e2e_fake_sidecars.py"
pass "fake sidecar probe"

docker compose "${COMPOSE_FILES[@]}" exec -T api cat /app/backend/.e2e-results/fake-sidecars-report.json \
  > "$BACKEND_DIR/.e2e-results/fake-sidecars-report.json" || true

echo ""
echo "All fake sidecar E2E checks passed."
