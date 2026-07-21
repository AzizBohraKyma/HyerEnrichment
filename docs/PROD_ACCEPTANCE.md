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
| `/health` 200 | PASS (local dry run) | | 2026-07-21 | agent |
| `/ready` 200 | PASS (local dry run) | | 2026-07-21 | agent |
| Auth enrich 200 | PASS (local dry run) | | 2026-07-21 | agent |
| Opt-out no Bearer 202 | PASS (local dry run) | | 2026-07-21 | agent |
| DSAR no Bearer 201 | PASS (local dry run) | | 2026-07-21 | agent |
| Boundary pytest bundle | PASS (local dry run) | | 2026-07-21 | agent |
| Full-path E2E | PASS (local dry run + GHA 29563202825) | | 2026-07-21 | agent |
| Staging Scrapoxy | PASS (GHA 29563202825) | | 2026-07-17 | CI |
| Staging Langfuse | PASS (GHA 29563202825) | | 2026-07-17 | CI |
| Ops runbook reviewed ([OPS.md](OPS.md)) | PASS (docs on main) | | 2026-07-17 | |

### Local dry-run evidence (2026-07-21)

`bash scripts/prod_full_acceptance.sh --local` was run end-to-end against an
isolated Docker Compose project (`task90dryrun`, separate from any standing
dev stack) built from `backend/docker/docker-compose.prod.yml`, using a
local-only env file and dummy secrets — no real third-party credentials.
Every stage (`setup`, `compose_up`, `/ready`, `smoke_local`,
`boundary_checks`, `full_path_e2e`) passed with exit code 0 and the acceptance
report shows zero failures.

Evidence: [`backend/docs/e2e-evidence/prod-dryrun-2026-07-21/`](../backend/docs/e2e-evidence/prod-dryrun-2026-07-21/)
(full terminal transcript, `prod-acceptance-report.json`, `full-path-report.json`).

This confirms the deploy + acceptance **automation itself** (compose file,
env templates, acceptance/smoke/E2E scripts) is correct and complete. A few
real bugs found during this dry run were fixed on `main` via this PR — see
the PR description for details.

## Production evidence (fill when host live)

| Item | Value |
|------|--------|
| Host | **PENDING — awaiting VPS** |
| TLS issuer | |
| Acceptance run date | |
| Report JSON path | |
| PR links | #65 (87), #68 (88), #70 (89) |

**Status:** Local dry-run of the full deploy + acceptance path is now verified
end-to-end (see evidence above); staging proofs green. **Production BLOCKED**
— the only remaining blocker is provisioning a real VPS and pointing DNS at
`enrich.hyrepath.io`; this is an external/business decision that cannot be
closed by code changes (no VPS chosen as of 2026-07-21).

**Remaining live gates:** Multilogin Tier 1 canary ([SKIP](../backend/docs/evidence/tier1-multilogin-canary-skip.md)); prod VPS provisioning + DNS cutover (Tasks 86–89).
