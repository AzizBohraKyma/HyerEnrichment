# Load / performance testing (k6)

Fake concurrent traffic against the enrichment API to catch timeouts, queue backlog, and DB pressure before launch.

## What it covers

| Scenario | Endpoints | Purpose |
|----------|-----------|---------|
| Readiness baseline | `GET /health`, `GET /ready` | Ingress + Postgres/Redis under concurrency |
| Async enrichment | `POST /enrich` + poll `GET /enrich/{id}` | Queue + worker path |
| Sync enrichment | `POST /enrich/sync` (low VUs) | Inline pipeline latency |

Scripts live in [`backend/load/k6/main.js`](../load/k6/main.js). The runner writes [`backend/.e2e-results/load-report.json`](../.e2e-results/load-report.json).

## Prerequisites

- Docker Engine (WSL2 on Windows is fine)
- Repo checkout with Compose files under `backend/docker/`

Do **not** point this harness at production or enable live Tier 1 / Multilogin. Load runs use **fake sidecars** and a **loadtest compose override** that raises `MAX_*_REQUESTS_PER_MINUTE` so the test measures capacity, not the default 10/30/min rate limits.

## Quick start

From the repo root:

```bash
make load-test
```

Defaults to `LOAD_PROFILE=smoke` (short stages). For a heavier run:

```bash
LOAD_PROFILE=full make load-test
```

Useful env vars (see `backend/scripts/run_load_test.py`):

| Var | Default | Meaning |
|-----|---------|---------|
| `LOAD_PROFILE` | `smoke` | `smoke` or `full` stage sizes |
| `API_TOKEN` | `change-me` | Bearer token |
| `LOAD_KEEP_STACK` | `0` | `1` leaves Compose up after the run |
| `LOAD_SKIP_UP` | `0` | `1` skips `compose up` (stack already running) |
| `K6_IMAGE` | `grafana/k6:0.54.0` | k6 container image |

Manual Compose (equivalent stack):

```bash
cd backend/docker
docker compose -f docker-compose.yml -f docker-compose.fake-sidecars.yml \
  -f docker-compose.loadtest.yml --profile paid up --build -d \
  api worker redis postgres social-analyzer google-maps-scraper email-verifier reacher
LOAD_SKIP_UP=1 LOAD_KEEP_STACK=1 python ../scripts/run_load_test.py
```

## Interpreting results

- k6 exit code `0` and `thresholds_passed: true` in `load-report.json` means the configured thresholds passed.
- Key custom rates: `enrich_enqueue_ok`, `enrich_job_completed`, `enrich_sync_ok`.
- If jobs fail to complete under smoke, check worker logs and Redis/RQ backlog before raising VUs.

Harness contract tests (no Docker): `pytest backend/tests/test_load_harness.py`.

## CI

Optional manual workflow: [`.github/workflows/load-test.yml`](../../.github/workflows/load-test.yml) (`workflow_dispatch`). Not required on every PR.
