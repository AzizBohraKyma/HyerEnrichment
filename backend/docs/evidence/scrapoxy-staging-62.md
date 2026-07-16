# Evidence: Scrapoxy staging (Task 62)

**Branch:** `feat/scrapoxy-staging-62`  
**Date (UTC):** 2026-07-16  
**Runner:** `backend/scripts/e2e_scrapoxy.sh`

## Deliverables

- [`backend/docker/docker-compose.staging.yml`](../../docker/docker-compose.staging.yml) — Scrapoxy ports + healthcheck
- [`backend/scripts/e2e_scrapoxy.sh`](../../scripts/e2e_scrapoxy.sh) — staging proof script
- [`backend/.env.staging.example`](../../.env.staging.example) — `PROXY_MODE=scrapoxy` template

## Commands

```bash
# Set in backend/.env:
# PROXY_MODE=scrapoxy
# SCRAPOXY_URL=http://scrapoxy:8888

bash backend/scripts/e2e_scrapoxy.sh
pytest tests/test_enrichers.py -k scrapoxy -v
```

## Results (this host)

| Step | Status | Notes |
|------|--------|-------|
| `test_proxy_provider_scrapoxy_builds_authenticated_url` | **PASS** | Windows pytest (51-test suite includes scrapoxy) |
| Scrapoxy container up | **NOT RUN** | Docker daemon unavailable |
| `ProxyProvider.get()` in worker | **NOT RUN** | Requires compose |
| Live sherlock via proxy | **OPTIONAL** | EMPTY OK without Scrapoxy proxy fleet in commander |

## Pass criteria

- `e2e_scrapoxy.sh` exit 0
- `scrapoxy-report.json` written under `.e2e-results/`
- `ProxyProvider` returns non-empty URL when `PROXY_MODE=scrapoxy`

## Note

Scrapoxy commander must have an active **proxy project** for egress. Wiring proof (this script) is separate from fleet-backed enrichment volume.
