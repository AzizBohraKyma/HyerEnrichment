#!/usr/bin/env bash
# GlitchTip / Sentry-compatible error tracking E2E proof.
#
# Usage:
#   bash backend/scripts/e2e_error_tracking.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/../docker" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$BACKEND_DIR/.env"
REPORT="$BACKEND_DIR/.e2e-results/error-tracking-report.json"

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; exit 1; }

mkdir -p "$BACKEND_DIR/.e2e-results"
service docker start >/dev/null 2>&1 || true

[ -f "$ENV_FILE" ] || cp "$BACKEND_DIR/.env.example" "$ENV_FILE"

export ENABLE_TIER1=false
export GLITCHTIP_PUBLIC_URL="${GLITCHTIP_PUBLIC_URL:-http://localhost:8001}"
export GLITCHTIP_DATABASE_URL="${GLITCHTIP_DATABASE_URL:-postgresql://hyrepath:hyrepath@postgres:5432/glitchtip}"
export SENTRY_ENVIRONMENT="${SENTRY_ENVIRONMENT:-e2e}"
export SENTRY_RELEASE="${SENTRY_RELEASE:-e2e-error-tracking}"

cd "$COMPOSE_DIR"

docker compose --env-file "$ENV_FILE" -f docker-compose.yml up -d postgres redis
for i in $(seq 1 30); do
  docker compose -f docker-compose.yml exec -T postgres \
    pg_isready -U hyrepath -d hyrepath >/dev/null 2>&1 && break
  sleep 2
done
docker compose -f docker-compose.yml exec -T postgres \
  psql -U hyrepath -d hyrepath -tc "SELECT 1 FROM pg_database WHERE datname='glitchtip'" \
  | grep -q 1 \
  || docker compose -f docker-compose.yml exec -T postgres \
       psql -U hyrepath -d hyrepath -c "CREATE DATABASE glitchtip;"

docker compose --env-file "$ENV_FILE" -f docker-compose.yml \
  --profile observability up -d --build glitchtip-migrate glitchtip-web glitchtip-worker

code="000"
for i in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001 || true)"
  [ "$code" = "200" ] || [ "$code" = "307" ] && break
  sleep 5
done

write_report() {
  local status="$1"
  local dsn="${2:-}"
  local issue_count="${3:-0}"
  python3 - <<PY
import json, time
from pathlib import Path
Path(r"""$REPORT""").write_text(json.dumps({
  "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "glitchtip_url": "http://localhost:8001",
  "http_status": """$code""",
  "database": """$GLITCHTIP_DATABASE_URL""",
  "sentry_environment": """$SENTRY_ENVIRONMENT""",
  "sentry_release": """$SENTRY_RELEASE""",
  "dsn_configured": bool("""$dsn"""),
  "issue_count": int("""$issue_count"""),
  "exit_code": $status,
}, indent=2))
PY
}

[ "$code" = "200" ] || [ "$code" = "307" ] || {
  write_report 1 "" 0
  fail "GlitchTip UI not reachable (last=$code)"
}
pass "GlitchTip UI reachable"

bootstrap_output="$(docker compose -f docker-compose.yml exec -T glitchtip-web \
  ./manage.py shell < "$BACKEND_DIR/scripts/glitchtip_bootstrap_dsn.py" 2>/dev/null || true)"
SENTRY_DSN="$(printf '%s\n' "$bootstrap_output" | sed -n 's/^DSN=//p' | tail -1)"
[ -n "$SENTRY_DSN" ] || {
  write_report 1 "" 0
  fail "Could not bootstrap GlitchTip DSN"
}
pass "GlitchTip DSN bootstrapped"

export SENTRY_DSN
export ENABLE_ERROR_TRACKING_PROBE=true

docker compose --env-file "$ENV_FILE" -f docker-compose.yml \
  --profile observability up -d --build --force-recreate api worker

health_code="000"
for i in $(seq 1 60); do
  health_code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || true)"
  [ "$health_code" = "200" ] && break
  sleep 5
done
[ "$health_code" = "200" ] || {
  write_report 1 "$SENTRY_DSN" 0
  fail "API not healthy after SENTRY_DSN configure (last=$health_code)"
}
pass "API healthy with SENTRY_DSN"

probe_code="$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/internal/error-tracking-probe || true)"
[ "$probe_code" = "200" ] || {
  write_report 1 "$SENTRY_DSN" 0
  fail "Error tracking probe failed (last=$probe_code)"
}
pass "Error tracking probe accepted"

issue_count=0
for i in $(seq 1 30); do
  issue_count="$(docker compose -f docker-compose.yml exec -T glitchtip-web ./manage.py shell -c "
try:
    from issues.models import Issue
except ImportError:
    from apps.issues.models import Issue
print(Issue.objects.count())
" 2>/dev/null | tail -1 | tr -d '[:space:]')"
  [ "${issue_count:-0}" -gt 0 ] && break
  sleep 5
done

[ "${issue_count:-0}" -gt 0 ] || {
  write_report 1 "$SENTRY_DSN" 0
  fail "No GlitchTip issues recorded after probe"
}
pass "GlitchTip recorded issue (count=$issue_count)"

write_report 0 "$SENTRY_DSN" "$issue_count"
pass "error tracking E2E proof complete"
