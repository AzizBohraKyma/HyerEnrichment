# Evidence: ChangeDetection staging (Task 71 adjacent)

**Date (UTC):** 2026-07-17  
**Status:** **DEFERRED / not in Task 90 CI matrix**

## Notes

- Compose service: `changedetection` under `--profile observability` (`backend/docker/docker-compose.yml`).
- Helper: `backend/scripts/setup_changedetection_watches.py` (exists on main).
- Task 90 GHA workflow currently proves Scrapoxy + Langfuse only; ChangeDetection product flow remains DEVPLAN gap **71**.

## When to mark PASS

1. `docker compose --profile observability up -d changedetection`
2. UI reachable on `:5000`
3. Webhook / watch setup script succeeds against local API
4. Attach short report under `backend/.e2e-results/`
