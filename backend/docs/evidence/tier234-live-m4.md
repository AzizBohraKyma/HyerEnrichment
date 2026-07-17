# Evidence: Tier 2-4 live E2E (M4-M10) — Task 90

**Date (UTC):** 2026-07-17  
**CI run:** https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29557737182  
**Job:** `tier234-live` — **failure** (first full CI attempt)

## Failures observed

| Step | Status | Root cause |
|------|--------|------------|
| unit_tests | FAIL | `make setup` installed base package only — no pytest (`.[dev]`) |
| probe_sidecars | PASS | — |
| tier2_e2e | FAIL | `EnrichmentRequest(username=…)` hit default all-tiers validation (`tier1 requires linkedin_url`) |
| tier3_e2e | PASS | 14/14 checks |
| strict_e2e | FAIL | Same EnrichmentRequest default-tiers validation |
| full_path_live | FAIL | Cascaded from strict |
| canary_score | FAIL | Host venv imported `app.enrichers` → selenium missing; canary not run in-container |
| strict_report_gate | false PASS | Treated missing report as pass |

## Fixes (this PR)

- `make setup` → `pip install -e ".[dev]"`
- E2E / probe / unit call sites pass scoped `requested_tiers`
- `e2e_canary_tier234.sh` runs canary inside api container
- `strict_report_gate` fails when report missing
- Richer verify step detail lines

## Re-verify

Re-trigger `Local verification (Task 90)` on main after merge; expect `tier234-live` + downstream `local-acceptance` green.
