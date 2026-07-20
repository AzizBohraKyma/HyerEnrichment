# Evidence: Tier 1 Multilogin live canary — Task 90

**Date (UTC):** 2026-07-17
**Status:** **SKIP / BLOCKED** — remaining live gate for Task 90

## Why skipped

- Multilogin credentials are **not configured** on the operator host or in CI secrets for this pass.
- Tier 1 skip-live verification already passed on Windows (shape / settings path).
- Do **not** commit `backend/docs/tier1_canary_set.json` or Multilogin / LinkedIn bot secrets.

## Unblock checklist

1. Set in local `backend/.env` (never commit): `ENABLE_TIER1=true`, Multilogin email/password/folder, LinkedIn bot email/password, `BROWSER_MODE=multilogin`.
2. Copy `tier1_canary_set.example.json` → gitignored `tier1_canary_set.json` with real public profile URLs.
3. Run: `python backend/scripts/verify_tier1_live.py --json` (or documented Tier 1 live Makefile target when present).
4. Attach report under `backend/.e2e-results/` and update this file to PASS with date.

## Relation to Task 90

Local/staging completion can proceed without Multilogin. **Full Task 90 / Phase 7** stays partial until this live canary passes **and** production host (86–89) is signed.
