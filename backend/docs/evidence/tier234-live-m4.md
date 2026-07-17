# Evidence: Tier 2-4 live E2E (M4-M10) — Task 90

**Date (UTC):** 2026-07-17  
**CI runs:**
- Pre-#92: https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29557737182
- Post-#92: https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29559236134
- Post-#93: https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29563202825
- Post-#94: (in flight / follow-up)

## Root cause (post-#93 / #94)

| Step | Status | Cause |
|------|--------|-------|
| unit_tests | FAIL | `from app.providers.linkedin.urls import …` still loaded `linkedin/__init__.py`, which eagerly imported selenium client/login |
| probe_sidecars | PASS | |
| tier2_e2e | PASS | |
| tier3_e2e | PASS | |
| strict_e2e | PASS | |
| canary_score | FAIL | 2 cells FAIL (likely CrossLinked/theHarvester SERP EMPTY); JobSpy ZipRecruiter 403 noise |
| strict_report_gate | PASS | failed=0 |
| staging Scrapoxy / Langfuse | PASS | |

Earlier failures (fixed in #92/#93): missing `[dev]` pytest, unscoped `requested_tiers`, redundant `full_path_live` GitHub API exhaustion, canary ValidationError on incomplete profiles.

## Fixes

- #93: drop redundant full_path_live; canary skip invalid requests; JobSpy/GitRecon EMPTY→SKIP
- #94: lazy `app.providers` LinkedIn exports; CrossLinked EMPTY→SKIP; soft CrossLinked in e2e_tier3
- Follow-up: lazy `app.providers.linkedin` package init (urls/types only); theHarvester EMPTY→SKIP; upload `tier234-canary.json` artifact

## Re-verify

Re-trigger `Local verification (Task 90)` on main after merge; expect `tier234-live` + `local-acceptance` green.
