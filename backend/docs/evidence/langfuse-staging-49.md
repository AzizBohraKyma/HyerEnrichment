# Evidence: Langfuse staging (Task 49)

**Date (UTC):** 2026-07-17
**Runner:** `backend/scripts/e2e_langfuse.sh` via GitHub Actions `Local verification (Task 90)`
**CI run (PASS):** https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29559236134
**Prior fail:** https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29557737182

## Status

| Step | Status | Notes |
|------|--------|-------|
| Observability profile + langfuse image | **PASS** | Post-#92 |
| UI `localhost:3000` | **PASS** | Dedicated `langfuse` Postgres DB |
| Report artifact | **PASS** | `langfuse-report.json` (`http_status` 200, exit 0) |

## Pass criteria

- `e2e_langfuse.sh` exit 0
- `langfuse-report.json` under `.e2e-results/`
- Langfuse UI HTTP 200/307 on `:3000`
- `trace()` smoke from worker
