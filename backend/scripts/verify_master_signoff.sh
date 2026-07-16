#!/usr/bin/env bash
# Master verification matrix — independent sign-off gate.
#
# Usage:
#   bash backend/scripts/verify_master_signoff.sh --with-tier1 --with-scrapoxy --with-langfuse --with-prod

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EVIDENCE="$BACKEND_DIR/docs/evidence/MASTER_SIGNOFF.md"

WITH_TIER1=0 WITH_SCRAPOXY=0 WITH_LANGFUSE=0 WITH_PROD=0
for arg in "$@"; do
  case "$arg" in
    --with-tier1) WITH_TIER1=1 ;;
    --with-scrapoxy) WITH_SCRAPOXY=1 ;;
    --with-langfuse) WITH_LANGFUSE=1 ;;
    --with-prod) WITH_PROD=1 ;;
  esac
done

mkdir -p "$BACKEND_DIR/docs/evidence"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
failures=0
: > "$EVIDENCE.tmp"

run_step() {
  local name="$1"; shift
  echo "== $name =="
  if "$@"; then
    echo "- [x] $name" >> "$EVIDENCE.tmp"
  else
    echo "- [ ] $name (FAILED)" >> "$EVIDENCE.tmp"
    failures=$((failures + 1))
  fi
}

{
  echo "# Master sign-off verification"
  echo ""
  echo "Generated: $started"
  echo ""
  echo "## Checklist"
} > "$EVIDENCE"

run_step pytest bash -c "cd '$BACKEND_DIR' && python3 -m pytest tests -q --tb=no"
run_step e2e_ci bash "$SCRIPT_DIR/e2e_full_path.sh" --ci"
[ "$WITH_TIER1" = "1" ] && run_step tier1_live bash -c "cd '$BACKEND_DIR' && python3 scripts/verify_tier1_live.py --json"
run_step tier234_unit bash -c "cd '$BACKEND_DIR' && python3 scripts/verify_tier234_live.py --skip-live"
run_step tier234_live bash -c "cd '$BACKEND_DIR' && python3 scripts/verify_tier234_live.py --json"
[ "$WITH_SCRAPOXY" = "1" ] && run_step scrapoxy bash "$SCRIPT_DIR/e2e_scrapoxy.sh"
[ "$WITH_LANGFUSE" = "1" ] && run_step langfuse bash "$SCRIPT_DIR/e2e_langfuse.sh"
[ "$WITH_PROD" = "1" ] && run_step prod_acceptance bash "$SCRIPT_DIR/prod_acceptance.sh"

cat "$EVIDENCE.tmp" >> "$EVIDENCE"
rm -f "$EVIDENCE.tmp"
echo "" >> "$EVIDENCE"
echo "## Summary" >> "$EVIDENCE"
echo "" >> "$EVIDENCE"
echo "- Failures: $failures" >> "$EVIDENCE"

exit "$failures"
