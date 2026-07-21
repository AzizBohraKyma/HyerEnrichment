# Evidence: Tier 1 Multilogin live canary — Task 90

**Date (UTC):** 2026-07-17, updated 2026-07-21
**Status:** **PARTIAL — not yet PASS.** Multilogin launcher is now reachable and credentials are configured;
real bugs were found and fixed against a live run, but the full 20-profile API+worker canary has not yet
been re-verified end-to-end. See
[`../e2e-evidence/tier1-live-2026-07-21/README.md`](../e2e-evidence/tier1-live-2026-07-21/README.md) for the
full write-up (live isolation-mode PASS, the API-path bugs found/fixed, and what's still outstanding).

## 2026-07-21 update

- Multilogin X launcher reachability and credentials are **no longer the blocker** (previously they were).
- Isolation-mode scrape (Multilogin + Selenium, no API/worker) passed live, 4/4, after correcting bad
  profile slugs in the local canary set.
- The full API + RQ worker path surfaced two more real, now-fixed bugs (SQLite `database is locked` under
  concurrent writes; a stale Redis pub/sub client crashing the worker's *next* job after any job failure).
- The Multilogin daily view budget was exhausted while diagnosing/fixing the above, so the fixes have not
  yet been re-verified against a fresh full-canary run. **Task 90's live Tier 1 gate remains unsigned** until
  that re-run passes with `summary.fail == 0`.

## Why originally skipped (2026-07-17, historical)

- Multilogin credentials were **not configured** on the operator host or in CI secrets for this pass.
- Tier 1 skip-live verification already passed on Windows (shape / settings path).
- Do **not** commit `backend/docs/tier1_canary_set.json` or Multilogin / LinkedIn bot secrets.

## Unblock checklist (remaining)

1. Reset/confirm Multilogin daily view budget is available for both pool profiles.
2. Re-run `python backend/scripts/e2e_tier1_canary.py --file backend/docs/tier1_canary_set.json --json`,
   `python backend/scripts/run_canary_score.py --tier tier1 --json`, and
   `python backend/scripts/verify_tier1_live.py --json` against the full 20-profile set with the fixes from
   `fix/task90-tier1-live-canary` applied.
3. Confirm `summary.fail == 0` (or equivalent) in the resulting report(s).
4. Save the report(s) under `backend/docs/e2e-evidence/tier1-live-<date>/` and update this file to a full
   PASS with that date.

## Relation to Task 90

Local/staging completion can proceed without Multilogin. **Full Task 90 / Phase 7** stays partial until this live canary passes **and** production host (86–89) is signed.
