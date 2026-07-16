# Production acceptance checklist

Signed acceptance for Phase 6 (DEVPLAN tasks 86–89). **Not complete until prod host is live and all steps PASS.**

## Prerequisites

- [ ] Task 86 — stack deployed to agreed host
- [ ] Task 87 — secrets/TLS/env parity ([deployment.md](deployment.md))
- [ ] Task 88 — smoke + boundary green ([PROD_SMOKE.md](PROD_SMOKE.md))

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
| `/health` 200 | | | | |
| `/ready` 200 | | | | |
| Auth enrich 200 | | | | |
| Opt-out no Bearer 202 | | | | |
| DSAR no Bearer 201 | | | | |
| Boundary pytest bundle | | | | |
| Full-path E2E | | | | |
| Ops runbook reviewed ([OPS.md](OPS.md)) | | | | |

## Production evidence (fill when host live)

| Item | Value |
|------|--------|
| Host | |
| TLS issuer | |
| Acceptance run date | |
| Report JSON path | |
| PR links | #65 (87), #68 (88), TBD (89) |

**Status:** BLOCKED — `enrich.hyrepath.io` DNS did not resolve at 2026-07-16 verification.
