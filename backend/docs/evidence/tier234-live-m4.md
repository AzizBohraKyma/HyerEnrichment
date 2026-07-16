# Evidence: Tier 2-4 live E2E (M4-M10)

**Branch:** `feat/tier234-live-e2e`  
**Date (UTC):** 2026-07-16  
**Runner:** `backend/scripts/verify_tier234_live.py` (Python; no bash/WSL for live chain)

## Environment

| Component | Status |
|-----------|--------|
| Docker | **BLOCKED** — `docker` not in PATH; Docker Desktop binary not found |
| `docker compose` (backend/docker) | **NOT RUN** — blocked by Docker |
| WSL | **BLOCKED** — unreliable on host (`Wsl/Service/E_UNEXPECTED` in prior runs) |
| API on `:8000` | Intermittent — available during partial native runs; **down** during final `verify_tier234_live.py --json` tier2 step |

## Commands run

```powershell
cd g:\ThunderMarketingCorp\HyerEnrichment\backend
python scripts/verify_tier234_live.py --skip-live --json
python scripts/e2e_tier2.py
python scripts/e2e_tier3.py
python scripts/e2e_realworld_strict.py
python scripts/run_canary_score.py --tier tier234 --json
python scripts/verify_tier234_live.py --json
```

Skipped (Docker blocked):

```powershell
cd g:\ThunderMarketingCorp\HyerEnrichment\backend\docker
docker compose --env-file ..\.env up -d api worker redis postgres social-analyzer google-maps-scraper email-verifier
```

## Step matrix (Sub-agent B)

| Step | Status | Exit / gate | Notes |
|------|--------|-------------|-------|
| Git: fetch, main, branch `feat/tier234-live-e2e` | **PASS** | — | Initial `index.lock` contention; branch created |
| Docker availability | **BLOCKED** | — | Not installed / not on PATH |
| `docker compose` sidecars | **BLOCKED** | — | Not executed |
| `verify_tier234_live.py --skip-live --json` | **FAIL** | 1 | Unit tests: 2 failed / 49 passed (first run); later 51 passed on branch tip |
| `e2e_tier2.py` | **FAIL** | 1 | 3 passed, 7 failed — sherlock/maigret CLIs missing; partial API enrichment |
| `e2e_tier3.py` | **FAIL** | 1 | 3 passed, 11 failed — Tier 3 CLIs/sidecars not on native Windows PATH |
| `e2e_realworld_strict.py` | **FAIL** | 1 | 15 passed, 1 failed — `GITRECON_SCRIPT` unset |
| `run_canary_score.py --tier tier234 --json` | **FAIL** | 1 | `tier234-canary.json`: profiles pass=0 fail=19 skip=1 |
| `verify_tier234_live.py --json` (live) | **FAIL** | 1 | See `verify-tier234-live.json`; bash probe paths broken on Windows Git bash |
| M4 gate `strict-report.json` `failed == 0` | **FAIL** | failed=1 | GitRecon strict check |

## `verify-tier234-live.json` (live, 2026-07-16T10:04:05Z)

- **unit_tests:** pass (51 passed)
- **probe_sidecars:** fail (bash path `G:ThunderMarketingCorp...` — no `/mnt/` translation)
- **tier2_e2e:** fail (`httpx.ConnectError` — API not reachable)
- **tier3_e2e:** fail (`crosslinked` not on PATH)
- **strict_e2e:** fail (`email-sleuth` not on PATH)
- **full_path_live:** fail (same bash path issue)
- **canary_score:** fail (`SyntaxError` when invoked via verify wrapper path)
- **strict_report_gate:** fail (`failed=1`)

## Report JSON paths

| Artifact | Path |
|----------|------|
| Verify matrix | `backend/.e2e-results/verify-tier234-live.json` |
| Tier 2 | `backend/.e2e-results/tier2-report.json` |
| Tier 3 | `backend/.e2e-results/tier3-report.json` |
| Strict real-world | `backend/.e2e-results/strict-report.json` |
| Canary tier234 | `backend/.e2e-results/tier234-canary.json` |
| Canary combined | `backend/.e2e-results/canary-run-score.json` |
| Run logs | `backend/.e2e-results/e2e_tier2-run.log`, `e2e_tier3-run.log`, `e2e_realworld_strict-run.log`, `canary_tier234-run.log`, `verify_tier234_live-full.log` |

## Pass criteria (not met)

- Docker stack up with sidecars
- `verify-tier234-live.json` → `exit_code: 0`
- `strict-report.json` → `"failed": 0`
- `run_canary_score.py --tier tier234` → meaningful pass summary (not all FAIL/SKIP)

## Operator checklist

1. Install **Docker Desktop**; confirm `docker info` in PowerShell.
2. `cd backend/docker; docker compose --env-file ..\.env up -d api worker redis postgres social-analyzer google-maps-scraper email-verifier`
3. Prefer Python-only live chain: run `e2e_tier2.py`, `e2e_tier3.py`, `e2e_realworld_strict.py`, then `run_canary_score.py --tier tier234 --json`, then `verify_tier234_live.py --json` (or fix `probe_sidecars` / `e2e_full_path` to use Python runners on Windows).
4. Confirm `strict-report.json` → `"failed": 0`.
