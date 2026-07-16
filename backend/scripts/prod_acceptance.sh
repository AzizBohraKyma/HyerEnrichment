#!/usr/bin/env bash
# Production acceptance checks (Tasks 86–88).
#
# Env:
#   BASE_URL   — e.g. https://enrich.hyrepath.io
#   API_TOKEN  — production Bearer token

set -euo pipefail

BASE_URL="${BASE_URL:-https://enrich.hyrepath.io}"
API_TOKEN="${API_TOKEN:-change-me}"
TIMEOUT="${SMOKE_TIMEOUT:-120}"
BASE_URL="${BASE_URL%/}"

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; exit 1; }

code="$(curl -s -o /tmp/prod-health.json -w '%{http_code}' "$BASE_URL/health" || echo 000)"
[ "$code" = "200" ] || fail "/health expected 200, got $code"
pass "/health"

code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/enrich/sync" \
  -H "Content-Type: application/json" \
  -d '{"username":"prod-smoke","requested_tiers":["tier2"]}' || echo 000)"
[ "$code" = "401" ] || fail "unauth enrich expected 401, got $code"
pass "unauth /enrich/sync → 401"

code="$(curl -s -o /tmp/prod-enrich.json -w '%{http_code}' -X POST "$BASE_URL/enrich/sync" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"prod-smoke","requested_tiers":["tier2"]}' || echo 000)"
[ "$code" = "200" ] || fail "auth /enrich/sync expected 200, got $code"
pass "auth /enrich/sync"

code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/api/opt-out" \
  -H "Content-Type: application/json" \
  -d '{"email":"prod-acceptance@example.com","reason":"prod smoke"}' || echo 000)"
[ "$code" = "401" ] && fail "opt-out must not require Bearer on production"
pass "POST /api/opt-out public (status=$code)"

echo "prod acceptance ok"
