# Evidence: Langfuse staging (Task 49)

**Branch:** `feat/langfuse-staging-49`  
**Date (UTC):** 2026-07-16  
**Runner:** `backend/scripts/e2e_langfuse.sh`

## Deliverables

- `backend/scripts/e2e_langfuse.sh`

## Commands

```bash
# backend/.env: LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
bash backend/scripts/e2e_langfuse.sh
```

## Results (this host)

| Step | Status | Notes |
|------|--------|-------|
| `providers.llm.trace()` | **EXISTS** | No-op until `LANGFUSE_*` set |
| Langfuse UI `:3000` | **NOT RUN** | Docker daemon unavailable |
| `trace()` smoke | **NOT RUN** | Requires compose observability profile |

## Pass criteria

- `e2e_langfuse.sh` exit 0
- `langfuse-report.json` under `.e2e-results/`
