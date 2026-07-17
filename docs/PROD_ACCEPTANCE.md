# Production acceptance checklist

Signed acceptance for Phase 6 (DEVPLAN tasks 86–89). **Production column not complete until prod host is live.** Local column tracks laptop/CI acceptance.

## Prerequisites

- [ ] Task 86 — stack deployed to agreed host — **PENDING** (no VPS chosen as of 2026-07-17)
- [x] Task 87 — secrets/TLS/env parity templates on `main` ([deployment.md](deployment.md)); live apply still pending host
- [x] Task 88 — smoke + boundary harness on `main` ([PROD_SMOKE.md](PROD_SMOKE.md)); prod URL pending host
- [x] Task 89 — acceptance runner + OPS on `main` ([OPS.md](OPS.md)); prod drill pending host

## Automated run

```bash
# Local (CI / operator laptop with Docker)
bash scripts/prod_full_acceptance.sh --local

# Production
BASE_URL=https://enrich.hyrepath.io API_TOKEN="$PROD_TOKEN" bash scripts/prod_full_acceptance.sh --prod
```

Expected report: `backend/.e2e-results/prod-acceptance-report.json` with `"status": "pass"`.

## Manual sign-off

| Check | Local | Production | Date | Operator |
|-------|-------|------------|------|----------|
| `/health` 200 | PENDING CI `local-acceptance` | | 2026-07-17 | |
| `/ready` 200 | PENDING CI | | | |
| Auth enrich 200 | PENDING CI | | | |
| Opt-out no Bearer 202 | PENDING CI | | | |
| DSAR no Bearer 201 | PENDING CI | | | |
| Boundary pytest bundle | PENDING CI | | | |
| Full-path E2E | PASS (GHA 29557737182) | | 2026-07-17 | CI |
| Ops runbook reviewed ([OPS.md](OPS.md)) | PASS (docs on main) | | 2026-07-17 | |

## Production evidence (fill when host live)

| Item | Value |
|------|--------|
| Host | **PENDING — awaiting VPS** |
| TLS issuer | |
| Acceptance run date | |
| Report JSON path | |
| PR links | #65 (87), #68 (88), #70 (89) |

**Status:** Local/staging path in progress via Task 90 GHA workflow. **Production BLOCKED** — no prod host / DNS as of 2026-07-17 (operator deferred VPS).
