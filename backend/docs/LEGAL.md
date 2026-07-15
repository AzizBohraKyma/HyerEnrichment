# Legal and Compliance

Hyrepath Enrichment — compliance reference for operators and developers.

**Version:** 0.2 (July 2026)

---

## Policy summary

- **Public data only** — public profiles, commits, and search results.
- **Customer-supplied identifiers only** — no unsolicited people-finding.
- **Opt-out is permanent** — once registered, the identifier is blocked across all tiers.
- **Data erasure on opt-out** — matching job dossiers, photo cache, and R2/local assets are purged.
- **LGPD / GDPR / CCPA** — data subject requests supported via opt-out and DSAR endpoints.

---

## Authentication (v1)

Enrichment routes (`/enrich`, `/enrich/sync`, …) require **Bearer token** authentication (`Authorization: Bearer <API_TOKEN>`).

`POST /api/opt-out`, `GET /api/opt-out/check`, `POST /api/dsar`, and `GET /api/dsar/{id}` are **unauthenticated** so data subjects can exercise rights without an API key. They are protected by an IP-scoped rate limit (`MAX_COMPLIANCE_REQUESTS_PER_MINUTE`, default 20).

The public frontend form at `/opt-out` proxies requests to the backend (the BFF may still send a server-side token; it is not required for these routes).

---

## Identifier normalization

All suppression, purge, and audit hashing uses `app/compliance/identifiers.py`:

| Input | Canonical form |
|-------|----------------|
| Email | `strip().lower()` |
| LinkedIn URL | `linkedin:{slug}` via `extract_linkedin_slug()` |
| Username / company / business / job_search | `strip().lower()` |

LinkedIn URL variants (with/without `www`, trailing slash) hash identically.

**Note:** Opt-out is per submitted identifier. Opting out an email does not block enrichment by username unless that username is also opted out.

---

## What purge deletes

On opt-out or DSAR deletion:

1. **Jobs** — matching rows in `jobs` get `dossier_payload = {}` and `status = purged`
2. **Photo cache** — `photo_cache` SQL rows and Redis `tier1:photo:*` keys
3. **Object storage** — R2 objects (or local `.asset-cache/` files) referenced by `asset_key`

Suppression list entries are **never** deleted.

---

## Audit logging

Events are stored in SQL table `audit_logs` (no raw PII — only `identifier_hash` and job IDs):

- `opt_out`
- `data_purged`
- `dsar_created` / `dsar_completed`
- `enrichment_suppressed`

**Retention:** 5 years by default (`AUDIT_LOG_RETENTION_YEARS=5`).

**Cleanup:** Run periodically via cron:

```bash
cd backend && python scripts/purge_audit_logs.py
```

---

## DSAR (30-day SLA)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/dsar` | Create access or deletion request |
| `GET /api/dsar/{id}` | Poll status and summary |

**v1 behavior:** Requests are processed immediately on create (automated self-hosted stack).

- **Access** — returns job count, date range, and photo-cached flag (no dossier PII).
- **Deletion** — runs suppression + purge, same as opt-out.

Manual review queues and email notifications are deferred.

**Escalation:** For requests that cannot be satisfied automatically, contact your Hyrepath operator with the DSAR id from the API response.

---

## Enforcement in code

1. `PipelineOrchestrator._is_suppressed()` runs before any tier dispatch.
2. `POST /enrich` pre-checks suppression and returns `status: suppressed` without enqueueing.
3. `register_opt_out()` writes suppression, audits, and purges stored data.

See `backend/docs/ARCHITECTURE.md` for architecture details.

---

## Product boundaries

1. No face recognition.
2. No bulk scraping.
3. No private data sources.
4. No enrichment without a customer-supplied identifier.
