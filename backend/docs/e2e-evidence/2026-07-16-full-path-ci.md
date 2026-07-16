# Full-path E2E evidence (CI mode)

Developer Guide **Task 78** / DEVPLAN gap **78**.

## Run

- **Date (UTC):** 2026-07-16
- **Harness:** `backend/scripts/e2e_full_path_runner.py --ci`
- **Make target:** `make e2e-full-path` (repo root)
- **Host:** Windows 10; **Docker:** WSL2 (native Windows `docker` not on PATH)
- **Command:**

```bash
wsl bash -lc 'cd /mnt/g/ThunderMarketingCorp/HyerEnrichment/backend && export DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 && python3 scripts/e2e_full_path_runner.py --ci'
```

## Aggregate report

Generated at `2026-07-16T09:52:42Z` (mode `ci`).

| Metric | Value |
|--------|-------|
| passed | 2 |
| failed | 0 |
| skipped | 0 |

### Stages

| Stage | Script | OK | Exit | Duration (s) |
|-------|--------|----|------|--------------|
| compose_test | e2e_compose_test.sh | True | 0 | 731.49 |
| fake_sidecars | e2e_fake_sidecars.sh | True | 0 | 618.73 |

## Path covered

1. **compose_test** — API health, async enqueue/poll (queue + worker), opt-out suppression/purge, Postgres durability after worker restart.
2. **fake_sidecars** — Compose fake sidecar stack, tier integration probes, async tier-4 job with fixture business data.

## Raw JSON

```json
{
  "generated_at": "2026-07-16T09:52:42Z",
  "mode": "ci",
  "stages": [
    {
      "name": "compose_test",
      "script": "e2e_compose_test.sh",
      "ok": true,
      "exit_code": 0,
      "duration_seconds": 731.49,
      "skipped": false,
      "skip_reason": null,
      "child_report": null
    },
    {
      "name": "fake_sidecars",
      "script": "e2e_fake_sidecars.sh",
      "ok": true,
      "exit_code": 0,
      "duration_seconds": 618.73,
      "skipped": false,
      "skip_reason": null,
      "child_report": "fake-sidecars-report.json"
    }
  ],
  "passed": 2,
  "failed": 0,
  "skipped": 0
}
```

