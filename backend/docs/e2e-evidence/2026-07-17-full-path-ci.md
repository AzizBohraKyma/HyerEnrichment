# Full-path E2E CI evidence — 2026-07-17

## Commands

Local (WSL + rootless Podman, before host filesystem crash):

```bash
export DOCKER_HOST=unix:///run/user/1000/podman/podman.sock
export DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0
make e2e-full-path
```

GitHub Actions (authoritative green re-run after WSL crash):

- Workflow: `Local verification (Task 90)`
- Run: https://github.com/1Touch-dev/HyerPathEnrichment/actions/runs/29557737182
- Job: `e2e-full-path` — **success** (2026-07-17)

## Environment

| Field | Value |
|-------|-------|
| Local OS | Windows 10 (WSL2 Ubuntu + rootless Podman) |
| CI OS | `ubuntu-latest` (GitHub Actions) |
| Runner | `backend/scripts/e2e_full_path_runner.py --ci` |
| Related fix | PR #88 — tier-specific `requested_tiers` in fake sidecar enricher probes |

## Report summary (GHA artifact `full-path-report`)

Source: `backend/.e2e-results/full-path-report.json`

| Field | Value |
|-------|-------|
| `generated_at` | 2026-07-17T05:40:47Z |
| `mode` | ci |
| `passed` | 2 |
| `failed` | 0 |
| `skipped` | 0 |

## Stages (GHA)

| Stage | Script | OK | Exit | Duration (s) |
|-------|--------|----|------|--------------|
| compose_test | e2e_compose_test.sh | true | 0 | 164.31 |
| fake_sidecars | e2e_fake_sidecars.sh | true | 0 | 104.07 |

## Local Podman run (earlier same day)

| Field | Value |
|-------|-------|
| `generated_at` | 2026-07-17T04:48:36Z |
| `passed` / `failed` | 2 / 0 |
| compose_test | 63.32s |
| fake_sidecars | 32.69s |

## Verdict

**PASS** — Task 78 full-path CI green on Podman/WSL and confirmed again on GitHub Actions run `29557737182`.
