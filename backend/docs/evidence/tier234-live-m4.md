# Evidence: Tier 2-4 live E2E (M4-M10) — Task 90

**Date (UTC):** 2026-07-17  
**CI runs:**
- First attempt: https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29557737182 (pre-#92)
- Post-#92: https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29559236134

## Progress after PR #92

| Step | Post-#92 | Notes |
|------|----------|-------|
| unit_tests | FAIL | Host venv `[dev]` only; `conftest` → `runner` → LinkedIn selenium import |
| probe_sidecars | PASS | |
| tier2_e2e | PASS | 10/10 |
| tier3_e2e | PASS | 14/14 |
| strict_e2e | PASS | 16/16 |
| full_path_live | FAIL | Redundant re-run of tier2/3/strict; gitrecon GitHub API exhausted |
| canary_score | FAIL | `EnrichmentRequest` ValidationError on profiles missing identifiers; JobSpy WAF noise |
| strict_report_gate | PASS | failed=0 |
| staging Scrapoxy / Langfuse | PASS | Artifacts on run 29559236134 |

## Fixes (follow-up PR)

- Lazy-load selenium in `LinkedInPhotoEnricher` so unit tests do not need `[enrichers]`
- Drop redundant `full_path_live` from `verify_tier234_live.py` (already covered by tier2/3/strict)
- Canary: skip enrichers whose fields cannot form a valid `EnrichmentRequest`; treat JobSpy/GitRecon EMPTY as SKIP in CI
- Example canary rows: add `company` where crosslinked/theharvester are listed

## Re-verify

Re-trigger `Local verification (Task 90)` on main after merge; expect `tier234-live` + `local-acceptance` green.
