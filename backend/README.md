# Hyrepath Enrichment Backend

FastAPI backend for asynchronous and synchronous enrichment dossier generation.

## Run locally

Local dev uses SQLite by default (see `.env.example`) — no Postgres needed.

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Run with Docker Compose (Postgres + Redis)

API and worker images build from the `backend/` directory (not the repo root), so
local virtualenvs and frontend assets are not sent to Docker.

API and worker share one Postgres instance so async `POST /enrich` jobs can be
polled across processes. Job data survives restarts via the `postgres_data` volume.

```bash
cd backend/docker
docker compose up --build api worker redis postgres
```

### Worker Scaling

**Single-queue mode (default):** All workers process jobs from one shared queue.

```bash
# Scale workers horizontally (4 workers processing any tier)
docker compose up -d --scale worker=4
```

**Tier-specific workers:** Dedicated worker pools per tier with separate concurrency levels.

```bash
# Deploy with tier-specific workers
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  -f docker-compose.tier-workers.yml \
  up -d

# Tier 1 (browser): 2 workers
# Tier 2-4 (API): 6 workers (configurable via deploy.replicas)
```

**Environment variables for tier-specific routing:**

```bash
# Queue routing mode (default: single)
WORKER_QUEUE_MODE=per_tier  # or "single"

# For per_tier mode, each worker specifies its queue
WORKER_TARGET_QUEUE=tier1    # or "tier234"
```

See `docker-compose.tier-workers.yml` for the tier-specific worker configuration.

Then:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/enrich \
  -H "Authorization: Bearer change-me" \
  -H "Content-Type: application/json" \
  -d '{"username": "jane-doe"}'
# poll with the returned job id until status is "completed"
curl http://localhost:8000/enrich/<job_id> -H "Authorization: Bearer change-me"
```

## Test

```bash
make test
# or: cd backend && pytest tests -m "not postgres" -q --cov=app --cov-report=term-missing
```

CI enforces a line-coverage floor for `app/` via `fail_under` in `pyproject.toml`.

Architecture decisions (why Redis vs in-process, SQLite vs Postgres, etc.): [`docs/adr/README.md`](../docs/adr/README.md).

Change-signal ops (changedetection.io → `NOTIFY_WEBHOOK_URL`): see [ARCHITECTURE.md — Change signals](docs/ARCHITECTURE.md#change-signals-changedetectionio).

Tier 2–4 debugging (prerequisites, isolation probes, tier-by-tier API curls): [`docs/TESTING_TIER234.md`](docs/TESTING_TIER234.md). Tier 2 full E2E: `bash scripts/e2e_tier2.sh`. Tier 3 full E2E: `bash scripts/e2e_tier3.sh`.

```bash
cd backend
python scripts/probe_enrichers.py
python scripts/probe_enrichers.py --prereqs
```
