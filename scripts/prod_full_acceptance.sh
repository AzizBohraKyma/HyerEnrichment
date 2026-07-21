#!/usr/bin/env bash
# Full production acceptance meta-runner (local or prod).
#
# Usage:
#   bash scripts/prod_full_acceptance.sh --local
#   BASE_URL=https://enrich.hyrepath.io API_TOKEN=... bash scripts/prod_full_acceptance.sh --prod
#
# Report: backend/.e2e-results/prod-acceptance-report.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
RESULTS_DIR="$BACKEND_DIR/.e2e-results"
REPORT="$RESULTS_DIR/prod-acceptance-report.json"
MODE="${1:---local}"

case "$MODE" in
  --local)
    export BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
    export API_TOKEN="${API_TOKEN:-change-me}"
    E2E_MODE="--ci"
    RUN_FULLSTACK="${RUN_FULLSTACK:-1}"
    ;;
  --prod)
    if [ -z "${BASE_URL:-}" ] || [ -z "${API_TOKEN:-}" ]; then
      echo "BASE_URL and API_TOKEN are required for --prod" >&2
      exit 1
    fi
    export SMOKE_PROD=1
    E2E_MODE="${E2E_MODE:---live}"
    RUN_FULLSTACK="${RUN_FULLSTACK:-0}"
    ;;
  *)
    echo "Usage: $0 [--local|--prod]" >&2
    exit 2
    ;;
esac

mkdir -p "$RESULTS_DIR"
STARTED="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
FAILURES=0

run_step() {
  local name="$1"
  shift
  echo "== $name =="
  if "$@"; then
    echo "PASS  $name"
  else
    echo "FAIL  $name" >&2
    FAILURES=$((FAILURES + 1))
  fi
}

cd "$REPO_ROOT"

if [ "$MODE" = "--local" ]; then
  run_step setup make setup
  run_step compose_up make up
  echo "== wait for /ready =="
  ready=0
  for _ in $(seq 1 60); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/ready" || true)"
    if [ "$code" = "200" ]; then
      ready=1
      break
    fi
    sleep 2
  done
  if [ "$ready" -ne 1 ]; then
    echo "FAIL  /ready never returned 200" >&2
    FAILURES=$((FAILURES + 1))
  else
    echo "PASS  /ready"
  fi
fi

# --local runs against the compose stack's localhost BASE_URL; `make smoke-prod`
# forces SMOKE_PROD=1, which smoke_test.py rejects for localhost URLs by design
# (it's meant to catch operators accidentally "smoke-testing prod" against their
# laptop). Local mode wants the same checks without that production guard.
if [ "$MODE" = "--prod" ]; then
  run_step smoke_prod make smoke-prod
else
  run_step smoke_local make smoke
fi
run_step boundary_checks make boundary-checks

if [ -f "$BACKEND_DIR/scripts/e2e_full_path.sh" ]; then
  run_step full_path_e2e bash "$BACKEND_DIR/scripts/e2e_full_path.sh" "$E2E_MODE"
else
  echo "SKIP  full_path_e2e (script missing on branch)"
fi

if [ "$RUN_FULLSTACK" = "1" ] && [ -f "$SCRIPT_DIR/fullstack_e2e.sh" ]; then
  run_step frontend_integration bash "$SCRIPT_DIR/fullstack_e2e.sh"
fi

COMPLETED="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
python3 - <<PY
import json
from pathlib import Path
report = {
    "mode": "$MODE",
    "base_url": "$BASE_URL",
    "started_at": "$STARTED",
    "completed_at": "$COMPLETED",
    "failures": $FAILURES,
    "status": "pass" if $FAILURES == 0 else "fail",
}
Path(r"$REPORT").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"report: $REPORT")
PY

if [ "$FAILURES" -ne 0 ]; then
  echo "prod full acceptance FAILED ($FAILURES steps)" >&2
  exit 1
fi

echo "prod full acceptance ok"
