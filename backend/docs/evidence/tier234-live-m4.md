# Evidence: Tier 2–4 live E2E (M4–M10)

**Branch:** `feat/tier234-live-e2e-m4`  
**Date (UTC):** 2026-07-16  
**Runner:** `backend/scripts/verify_tier234_live.py`

## Commands run

```powershell
cd g:\ThunderMarketingCorp\HyerEnrichment\backend
python scripts/verify_tier234_live.py --skip-live --json
```

```bash
# Live chain (requires Docker daemon — WSL reported podman socket missing on this host)
bash backend/scripts/e2e_full_path.sh --live
```

## Results

| Step | Status | Notes |
|------|--------|-------|
| Unit tests (shape, tier2/3 merge, enrichers) | **PASS** | 51 passed (Windows Python 3.13) |
| `probe_sidecars.sh` | **NOT RUN** | Docker API unavailable in WSL (`podman.sock` missing) |
| `e2e_tier2.sh` | **NOT RUN** | Requires Docker |
| `e2e_tier3.sh` | **NOT RUN** | Requires Docker |
| `e2e_realworld_strict.sh` | **NOT RUN** | Requires Docker |
| `e2e_full_path.sh --live` | **NOT RUN** | Requires Docker |
| `strict-report.json` `failed: 0` | **PENDING** | Gate for M4 sign-off |

## Operator checklist

1. Start **Docker Desktop** or Docker Engine in WSL (`unix:///var/run/docker.sock`).
2. Run:
   ```bash
   cd backend
   python scripts/verify_tier234_live.py --json
   ```
   Or Windows-friendly live chain:
   ```powershell
   python scripts/e2e_full_path_runner.py --live
   ```
3. Confirm `backend/.e2e-results/full-path-report.json` — all live stages pass.
4. Confirm `backend/.e2e-results/strict-report.json` → `"failed": 0`.

## Pass criteria

- `verify-tier234-live.json` → `exit_code: 0`
- `full-path-report.json` live stages all pass
- `run_canary_score.py --tier tier234` → meaningful pass summary (not all SKIP)

## Artifacts

- `backend/.e2e-results/verify-tier234-live.json` (unit-only run recorded)
