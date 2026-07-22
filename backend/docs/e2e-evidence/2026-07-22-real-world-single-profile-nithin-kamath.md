# Evidence: Real-world single-profile Tier 1-4 run — Nithin Kamath (Zerodha)

**Date (UTC):** 2026-07-22
**Profile:** Nithin Kamath, CEO, Zerodha — `https://www.linkedin.com/in/nithin-kamath-81136242/`
**Scope:** ONE real profile through the real `POST /enrich` → RQ worker → real enricher CLIs/sidecars path — not the 20-profile canary set (`backend/docs/tier234_canary_set.example.json`).

## Setup: production-shaped local stack

Ran locally under WSL2 Ubuntu + Docker Engine, using a new production overlay (base compose + `docker-compose.prod.yml` [+ `docker-compose.tier1.yml`]) instead of the free-mode dev compose:

1. `backend/.env.production` (gitignored — `.env.*` is excluded by root `.gitignore`) — production overrides (`APP_ENV=production`, strong `API_TOKEN`, `DATABASE_URL`/`REDIS_URL` pointed at the compose `postgres`/`redis` services, `POSTGRES_USER`/`PASSWORD`) layered on top of the real secrets already in `backend/.env` (Multilogin, LinkedIn bot, GitHub, R2, LiteLLM/Gemini/OpenAI keys).
2. `backend/scripts/start_production.sh` — new reusable "run the backend for production" entrypoint: brings up `migrate api worker redis postgres social-analyzer google-maps-scraper email-verifier` with the prod overlay (+ tier1 overlay when `ENABLE_TIER1=true`), validates required env vars fail-fast, waits for `/health` = 200, auto-detects the Windows host IP for Multilogin under WSL2.
3. `backend/scripts/run_real_world_single_profile.py` — sends exactly one `POST /enrich` for this profile with `requested_tiers`, polls `GET /enrich/{id}` to completion, prints/writes the full merged dossier.
4. `backend/scripts/run_real_world_single_profile.sh` — wrapper: brings up the prod+tier1 stack via `start_production.sh`, waits for sidecar health from inside the compose network (sidecars have `ports: []` in prod), then runs the Python client inside the `api` container (which already has httpx + the app installed; the WSL host itself lacks `python3-venv`).

Identifiers beyond `linkedin_url`/name/role/company were filled from public-record best guesses (`username=Nithin0dha` — his real X/Twitter handle; `business="Zerodha Bengaluru"`), consistent with what a real customer request would supply.

## Fixes needed to make the prod overlay actually work

- `docker-compose.prod.yml`: Compose merges `ports:` lists across `-f` files by **concatenation**, not override. A bare `ports:` on `api`/`social-analyzer`/`google-maps-scraper`/`email-verifier` in the overlay was *adding* to the base compose's mapping instead of replacing it, so `api` tried to bind both `0.0.0.0:8000` and `127.0.0.1:8000` and failed to start. Fixed with the Compose spec `!override` merge tag (Docker Compose v2.24+).
- `migrate` service was using its own hardcoded dev `DATABASE_URL` instead of picking up the production Postgres password, so it failed auth against the freshly-initialized prod Postgres volume. Added an explicit `DATABASE_URL: ${DATABASE_URL:?set DATABASE_URL}` override.

## Result: Tiers 2-4 — PASS

Full terminal output: [`2026-07-22-real-world-single-profile-nithin-kamath/terminal-output.txt`](2026-07-22-real-world-single-profile-nithin-kamath/terminal-output.txt)
Structured report: [`2026-07-22-real-world-single-profile-nithin-kamath/real-world-single-profile-report.json`](2026-07-22-real-world-single-profile-nithin-kamath/real-world-single-profile-report.json)

- `job_id=job_566d095d13744a678acac9f144a458d4`, completed in **180.7s**
- **Tier 2** (handle hunt — Sherlock, Maigret, Social-Analyzer): 18 cross-source social handles for `Nithin0dha` (Bluesky, Twitter/X, Telegram, Product Hunt, Mastodon, Facebook, etc.), avg confidence 0.84, identity-match confidence **0.91**
- **Tier 3** (OSINT + email — theHarvester, CrossLinked, Email Sleuth, Email Verify): 76 `@zerodha.com` emails discovered, 76 coworker names extracted, 10 spot-verified (9 deliverable, 1 disposable), email-verification confidence **0.89**
- **Tier 4** (jobs + business — JobSpy, Google Maps Scraper): no open job postings matched; real business record returned for **Zerodha Fund House** (Bengaluru address, website, 4.1 rating) via Google Maps Scraper
- `sources`: `CrossLinked, Email Sleuth, Email Verify, Google Maps Scraper, Maigret, Sherlock, Social Analyzer, theHarvester` — all real enricher CLIs/sidecars, no mocks, no canary fixtures
- Coverage confidence: **1.0** (all 4 tiers exercised at least one real source)

## Tier 1 — blocked by a Multilogin + WSL2 networking limitation (not fixed in this task)

Tier 1 (LinkedIn photo scrape via Multilogin) was attempted first with the Multilogin desktop app running and logged in on the Windows host. It repeatedly failed with `ConnectTimeoutError` reaching the per-profile Selenium debug port, even though:

- The Multilogin launcher's main API port (`45001`) is reachable from the WSL2 `worker` container (confirmed via direct `curl` from inside the container to the auto-detected Windows host IP).
- Login/profile-launch calls to `https://api.multilogin.com` and `https://launcher.mlx.yt:45001` succeed.

Root cause: Multilogin binds the **per-profile Selenium/CDP debug port** to `127.0.0.1` only on the Windows host. WSL2's virtual network can reach the Windows host's other listening ports via the detected gateway IP, but a socket bound to `127.0.0.1` (loopback-only) is by definition unreachable from any other network namespace, including WSL2's — regardless of host-IP routing. This exact class of limitation is already flagged in `backend/docker/docker-compose.tier1.yml`'s own comments ("On Windows Desktop, prefer a host-native RQ worker ... if Selenium Host-header checks fail").

**This is not a bug introduced by this task** — it is a pre-existing constraint of running the Tier 1 Multilogin worker inside WSL2/Docker on Windows. Resolving it for real would require running the RQ worker as a native Windows process (outside Docker/WSL) so it can reach `127.0.0.1:<selenium-port>` directly, which is a bigger infrastructure change than this task's scope. Per user decision, this run proceeded with Tiers 2-4 only; Tier 1 is documented here as a known follow-up.

## Reproduce

```bash
# WSL2 Ubuntu, Docker Engine, Multilogin desktop app running/logged in on Windows
wsl -d Ubuntu bash /mnt/g/ThunderMarketingCorp/HyerEnrichment/backend/scripts/run_real_world_single_profile.sh
# Tiers 2-4 only (skip Tier 1's Multilogin dependency):
#   pass --tiers tier2 tier3 tier4 to run_real_world_single_profile.py when invoking it directly
```
