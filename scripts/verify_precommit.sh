#!/usr/bin/env bash
# Verify pre-commit hooks: full sweep, negative cases, and helper scripts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x "${ROOT}/backend/.venv/bin/pre-commit" ]]; then
  PRE_COMMIT="${ROOT}/backend/.venv/bin/pre-commit"
  PYTHON="${ROOT}/backend/.venv/bin/python"
elif [[ -x "${ROOT}/backend/.venv/Scripts/pre-commit.exe" ]]; then
  PRE_COMMIT="${ROOT}/backend/.venv/Scripts/pre-commit.exe"
  PYTHON="${ROOT}/backend/.venv/Scripts/python.exe"
else
  echo "ERROR: run 'make setup' first (pre-commit not found in backend/.venv)" >&2
  exit 1
fi

echo "==> B: full-repo pre-commit sweep"
"$PRE_COMMIT" run --all-files

echo "==> C1: env guard rejects .env commits"
TMP_ENV="${ROOT}/backend/.env.precommit-test"
trap 'git reset -q HEAD -- "$TMP_ENV" 2>/dev/null || true; rm -f "$TMP_ENV"' EXIT
echo 'SECRET=test' >"$TMP_ENV"
git add -f "$TMP_ENV"
set +e
git commit -m "test: should block env file" >/dev/null 2>&1
status=$?
set -e
if [[ $status -eq 0 ]]; then
  echo "ERROR: env guard should have blocked commit" >&2
  exit 1
fi
git reset -q HEAD -- "$TMP_ENV"
rm -f "$TMP_ENV"

echo "==> C2: commit-msg hook rejects Co-authored-by"
CO_BAD="$(mktemp)"
printf 'test subject\n\nCo-authored-by: Agent <agent@example.com>\n' >"$CO_BAD"
set +e
"$PRE_COMMIT" run --hook-stage commit-msg no-co-authored-by --commit-msg-filename "$CO_BAD" >/dev/null 2>&1
co_status=$?
set -e
rm -f "$CO_BAD"
if [[ $co_status -eq 0 ]]; then
  echo "ERROR: commit-msg hook should reject Co-authored-by trailers" >&2
  exit 1
fi

echo "==> C3: block_co_authored_by.py accepts plain messages"
CO_OK="$(mktemp)"
printf 'test subject\n' >"$CO_OK"
"$PYTHON" scripts/hooks/block_co_authored_by.py "$CO_OK"
rm -f "$CO_OK"

echo "==> C4: block_co_authored_by.py rejects Co-authored-by"
CO_BAD="$(mktemp)"
printf 'test subject\n\nCo-authored-by: bot <bot@example.com>\n' >"$CO_BAD"
set +e
"$PYTHON" scripts/hooks/block_co_authored_by.py "$CO_BAD" >/dev/null 2>&1
bad_status=$?
set -e
rm -f "$CO_BAD"
if [[ $bad_status -eq 0 ]]; then
  echo "ERROR: block_co_authored_by.py should fail on Co-authored-by" >&2
  exit 1
fi

echo "All pre-commit verification checks passed."
