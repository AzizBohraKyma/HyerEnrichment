# Fresh-setup verification

**Date:** 2026-07-16  
**Branch:** `chore/fresh-setup-verify`  
**Merged into worktree (not GitHub PRs):** `origin/feat/makefile-dev-targets`, `origin/feat/expand-smoke-test`  
**Result:** PASS

## Environment

| Item | Value |
|------|--------|
| Host OS | Windows 10 (build 26200) |
| Runtime | WSL2 Ubuntu (rootless Podman via `DOCKER_HOST=unix:///run/user/1000/podman/podman.sock`) |
| Make | GNU Make 4.4.1 (WSL) |
| Python (setup/smoke) | 3.14 via `backend/.venv` |
| Docker CLI | 29.1.3 talking to Podman 5.7.0 |
| Native Windows Docker Desktop | Not installed / not on PATH |
| Native Windows GNU Make | Not on PATH |

Notes:

- Documented path `make setup` → `make up` → `make smoke` was followed from the worktree under WSL (`/mnt/c/Users/AZIZ/.cursor/worktrees/...`).
- First `make setup` failed on PEP 668 (`externally-managed-environment`). Makefile now creates `backend/.venv` and installs there; also installs `requests` for `smoke_test.py`.
- First `make up` with BuildKit/Bake failed under Podman (shared `buildx_buildkit_default` name collision). Makefile `up` now sets `DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0` and runs detached (`-d`) so health wait + smoke can proceed.
- Real Docker Engine in WSL exists but requires interactive `sudo` (user not in `docker` group); verification used rootless Podman instead.

## Commands run

```bash
git fetch origin
git checkout -b chore/fresh-setup-verify origin/main
git merge origin/feat/makefile-dev-targets
git merge origin/feat/expand-smoke-test

export DOCKER_HOST=unix:///run/user/1000/podman/podman.sock
make setup
make up
# wait until curl http://127.0.0.1:8000/health → {"status":"ok",...}
make smoke
# extra enrich (beyond smoke username):
backend/.venv/bin/python -c "import requests,json; r=requests.post('http://127.0.0.1:8000/enrich/sync', headers={'Authorization':'Bearer change-me'}, json={'username':'fresh-setup-verify','requested_tiers':['tier2']}, timeout=60); print(r.status_code); print(r.json()['status'])"
```

## Results

| Step | Result | Evidence |
|------|--------|----------|
| `make setup` | PASS | Created `backend/.env`, `backend/.venv`; installed editable backend + `requests` |
| `make up` | PASS | Free stack up: api, worker, redis, postgres, social-analyzer, google-maps-scraper; postgres/redis healthy before api/worker |
| Wait healthy | PASS | `GET /health` → `{"status":"ok","service":"Hyrepath Enrichment Backend"}` |
| `make smoke` | PASS (exit 0) | See log excerpt below |
| Extra enrich | PASS | HTTP 200, `status: completed`, dossier with handles |

### `make smoke` log excerpt

```text
PASS  /health
PASS  unauth /enrich/sync → 401
PASS  /enrich/sync → completed
smoke ok
```

### Extra enrich excerpt

```text
200
status: completed
job id: job_369781d35f2545ef8f9d7d91fdef7ed7
dossier.handles present (Sherlock matches for username fresh-setup-verify)
```

## Doc / Makefile fixes applied during verification

1. **`Makefile` `setup`** — create/use `backend/.venv` (PEP 668), install `requests` for smoke.
2. **`Makefile` `up`** — detach (`-d`); disable BuildKit for Podman/classic builder compatibility.
3. **`Makefile` `smoke`** — prefer `backend/.venv/bin/python` when present.
4. **`README.md` Getting started** — document venv + detached `make up` + expanded smoke.

## Not done

- Did **not** merge any GitHub PRs (`#47`, `#49`, or this branch).
- Did **not** push to `main`.
