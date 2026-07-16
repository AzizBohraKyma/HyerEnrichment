# Evidence: Production deploy (Task 86)

**Branch:** `feat/prod-deploy-86`  
**Date (UTC):** 2026-07-16  
**Target:** https://enrich.hyrepath.io

## Deliverables

- [`docs/deployment.md`](../../../docs/deployment.md) — topology, compose, secrets, rollback
- [`backend/docker/docker-compose.prod.yml`](../../docker/docker-compose.prod.yml)
- [`backend/scripts/prod_acceptance.sh`](../../scripts/prod_acceptance.sh)

## Default topology (v1)

Linux VPS + Docker Compose + Cloudflare Tunnel → `api:8000`. Tier 1 MLX on separate Windows host (or `ENABLE_TIER1=false` until ready).

## Deploy steps (operator)

1. Provision VPS; install Docker.
2. Clone repo; copy production `.env` / `WORKER_ENV_FILE` (secrets not in git).
3. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
4. Configure Cloudflare Tunnel to `http://127.0.0.1:8000`; DNS `enrich.hyrepath.io`.
5. Run acceptance:
   ```bash
   BASE_URL=https://enrich.hyrepath.io API_TOKEN=<prod> bash backend/scripts/prod_acceptance.sh
   ```

## Results (this host)

| Step | Status | Notes |
|------|--------|-------|
| Deployment docs + prod compose | **DELIVERED** | In repo |
| `prod_acceptance.sh` | **DELIVERED** | Health, auth enrich, public opt-out, async poll |
| Live deploy to enrich.hyrepath.io | **PENDING** | No VPS/tunnel provisioned in this session |
| Prod acceptance exit 0 | **PENDING** | Run after deploy |

## Pass criteria (Tasks 86–88)

- `GET /health` → 200 on production URL
- Authenticated `/enrich/sync` tier2 smoke
- `POST /api/opt-out` without Bearer → not 401
- Async `/enrich` + poll `completed` when queue enabled
