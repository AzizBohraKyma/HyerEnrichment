#!/usr/bin/env bash
# Boundary pytest bundle - rate limits, compliance, tier hardening.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"
export DATABASE_URL="${BOUNDARY_DATABASE_URL:-sqlite+aiosqlite:///./.boundary-pytest.db}"
export REDIS_URL="${BOUNDARY_REDIS_URL:-redis://127.0.0.1:6379/15}"
export API_TOKEN="${BOUNDARY_API_TOKEN:-change-me}"
export APP_ENV="${BOUNDARY_APP_ENV:-development}"

rm -f .boundary-pytest.db

# `make setup` installs pytest into backend/.venv, but nothing puts that venv
# on PATH for this script — a bare `pytest` call silently depends on the
# caller's shell already having it available. Prefer the venv explicitly
# (same fallback pattern as the `smoke` Makefile target) so this works
# right after `make setup` on a clean machine/CI runner.
if [ -x "$BACKEND_DIR/.venv/bin/pytest" ]; then
  PYTEST="$BACKEND_DIR/.venv/bin/pytest"
else
  PYTEST="pytest"
fi

"$PYTEST" -q \
  tests/test_tier1_hardening.py \
  tests/test_gitrecon_throttle.py \
  tests/test_pipeline_shape.py \
  tests/test_opt_out_compliance.py \
  tests/test_dsar.py

echo "boundary checks ok"
