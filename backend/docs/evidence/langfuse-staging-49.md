# Evidence: Langfuse staging (Task 49)

**Date (UTC):** 2026-07-17  
**Runner:** `backend/scripts/e2e_langfuse.sh` via GitHub Actions `Local verification (Task 90)`  
**CI run:** https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29557737182

## Status (2026-07-17 first CI pass)

| Step | Status | Notes |
|------|--------|-------|
| Observability profile + langfuse image | **PASS** | Container started |
| UI `localhost:3000` | **FAIL** | Shared `hyrepath` Postgres DB — Langfuse schema conflict / crash loop |
| Report artifact | **MISSING** | Failed before JSON write |

## Follow-up

- Compose `DATABASE_URL` now defaults to dedicated `langfuse` database
- `e2e_langfuse.sh` creates that DB, force-recreates langfuse, writes report on failure
- Re-run via Task 90 workflow after merge

## Pass criteria

- `e2e_langfuse.sh` exit 0
- `langfuse-report.json` under `.e2e-results/`
- Langfuse UI HTTP 200/307 on `:3000`
- `trace()` smoke from worker
