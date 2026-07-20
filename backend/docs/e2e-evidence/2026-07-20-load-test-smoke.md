# Load-test evidence (k6 smoke) — 2026-07-20

## Command

```bash
# WSL Docker stack already up with fake-sidecars + docker-compose.loadtest.yml
LOAD_PROFILE=smoke LOAD_SKIP_UP=1 LOAD_KEEP_STACK=1 \
  python3 backend/scripts/run_load_test.py
```

## Result

- **Exit code:** 0
- **Profile:** smoke
- **Checks:** 100% (2724/2724)
- **enrich_enqueue_ok:** 100% (4/4)
- **enrich_job_completed:** 100% (4/4)
- **enrich_jobs_completed_count:** 4
- **enrich_sync_ok:** 100% (4/4)
- **enrich_sync_ok_count:** 4
- **http_req_failed:** 0%
- **health p95:** ~6ms; **ready p95:** ~27ms; **enrich_sync p95:** ~34s

Artifacts (gitignored): `backend/.e2e-results/load-report.json`, `backend/.e2e-results/k6-summary.json`.

Harness contract: `pytest backend/tests/test_load_harness.py` — 5 passed.
