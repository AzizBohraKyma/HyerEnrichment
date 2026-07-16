#!/usr/bin/env bash
# Langfuse staging proof (Task 49).
#
# Usage:
#   bash backend/scripts/e2e_langfuse.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/../docker" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$BACKEND_DIR/.env"
REPORT="$BACKEND_DIR/.e2e-results/langfuse-report.json"

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; exit 1; }
warn() { echo "WARN  $1"; }

mkdir -p "$BACKEND_DIR/.e2e-results"
service docker start >/dev/null 2>&1 || true

[ -f "$ENV_FILE" ] || cp "$BACKEND_DIR/.env.example" "$ENV_FILE"

export ENABLE_TIER1=false
export LANGFUSE_HOST="${LANGFUSE_HOST:-http://langfuse:3000}"

cd "$COMPOSE_DIR"
profiles="--profile observability"
if grep -Eq '^OPENAI_API_KEY=.+' "$ENV_FILE" || grep -Eq '^GEMINI_API_KEY=.+' "$ENV_FILE"; then
  profiles="$profiles --profile llm"
fi

docker compose --env-file "$ENV_FILE" -f docker-compose.yml \
  $profiles up -d --build api worker redis postgres langfuse

if echo "$profiles" | grep -q llm; then
  docker compose --env-file "$ENV_FILE" -f docker-compose.yml --profile llm up -d litellm || true
fi

code="000"
for i in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || true)"
  [ "$code" = "200" ] || [ "$code" = "307" ] && break
  sleep 5
done
[ "$code" = "200" ] || [ "$code" = "307" ] || fail "langfuse UI not reachable (last=$code)"
pass "langfuse UI reachable"

docker compose -f docker-compose.yml exec -T worker \
  python -c "from app.providers.llm import trace; trace('e2e-langfuse-smoke', {'source': 'e2e_langfuse.sh'}); print('ok')"
pass "trace() smoke invoked"

python3 - <<PY
import json, time
from pathlib import Path
Path("""$REPORT""").write_text(json.dumps({
  "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "langfuse_url": "http://localhost:3000",
  "http_status": """$code""",
  "exit_code": 0,
}, indent=2))
PY
pass "langfuse staging proof complete"
