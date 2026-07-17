#!/usr/bin/env bash
# Tier 2–4 canary score inside the api container (scripts/docs are dockerignored).
#
# Usage:
#   bash backend/scripts/e2e_canary_tier234.sh
#
# Assumes compose api/worker/redis/postgres (+ free sidecars) are already up.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(cd "$SCRIPT_DIR/../docker" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$BACKEND_DIR/.env"
DOCS_DIR="$BACKEND_DIR/docs"
CANARY_EXAMPLE="$DOCS_DIR/tier234_canary_set.example.json"
CANARY_LOCAL="$DOCS_DIR/tier234_canary_set.json"
RESULTS_DIR="$BACKEND_DIR/.e2e-results"

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; exit 1; }
warn() { echo "WARN  $1"; }

mkdir -p "$RESULTS_DIR"
[ -f "$ENV_FILE" ] || cp "$BACKEND_DIR/.env.example" "$ENV_FILE"

if [ ! -f "$CANARY_LOCAL" ]; then
  cp "$CANARY_EXAMPLE" "$CANARY_LOCAL"
  warn "copied $CANARY_EXAMPLE -> $CANARY_LOCAL"
fi

cd "$COMPOSE_DIR"
export ENABLE_TIER1=false

echo "== wait for API health =="
code="000"
for i in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || true)"
  [ "$code" = "200" ] && break
  sleep 3
done
[ "$code" = "200" ] || fail "API health never returned 200 (last=$code)"
pass "api health 200"

echo "== stream canary JSON into api =="
docker compose --env-file "$ENV_FILE" exec -T api sh -c '
  mkdir -p /tmp/hyrepath-canary /app/backend/.e2e-results
  cat > /tmp/hyrepath-canary/tier234_canary_set.json
' < "$CANARY_LOCAL"

echo "== run probe_enrichers canary inside api =="
set +e
docker compose --env-file "$ENV_FILE" exec -T api sh -c '
  set -e
  cd /app/backend
  export E2E_BACKEND_ROOT=/app/backend
  python - --canary /tmp/hyrepath-canary/tier234_canary_set.json --json
' < "$SCRIPT_DIR/probe_enrichers.py"
probe_rc=$?
set -e

docker compose --env-file "$ENV_FILE" exec -T api \
  cat /app/backend/.e2e-results/tier234-canary.json \
  > "$RESULTS_DIR/tier234-canary.json" || true

# Combined score summary on the host (no selenium import path).
if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
  PY="$BACKEND_DIR/.venv/bin/python"
else
  PY=python3
fi
"$PY" - <<PY
import json, time
from pathlib import Path
results = Path(r"$RESULTS_DIR")
canary = results / "tier234-canary.json"
payload = {
  "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "dry_run": False,
  "tier": "tier234",
  "limit": None,
  "actions": {
    "tier234": {
      "canary_file": {"local": r"$CANARY_LOCAL", "action": "in-container"},
      "probe": {"status": "RAN", "exit_code": $probe_rc},
    },
    "tier1": {},
  },
  "results": {"tier234": {"status": "MISSING", "summary": {}}, "tier1": {"status": "NOT_RUN"}},
}
if canary.is_file():
    report = json.loads(canary.read_text(encoding="utf-8"))
    summary = report.get("summary") or {}
    fail = int(summary.get("cells_fail") or summary.get("profiles_fail") or 0)
    payload["results"]["tier234"] = {
        "status": "PASS" if fail == 0 else "FAIL",
        "summary": summary,
        "report_path": str(canary),
    }
else:
    raise SystemExit("tier234-canary.json missing after in-container probe")
(results / "canary-run-score.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(f"Combined report: {results / 'canary-run-score.json'}")
if $probe_rc != 0 or payload["results"]["tier234"]["status"] != "PASS":
    raise SystemExit(1)
PY

pass "tier234 canary score"
