# Frontend smoke checklist

Run with backend at `http://localhost:8000` and `BACKEND_API_TOKEN` matching `backend/.env`.

## Setup

```bash
cd frontend
cp .env.example .env.local
# set BACKEND_API_URL and BACKEND_API_TOKEN
npm run dev
```

## Checks

1. **Health** — Console header shows green "API online" when backend is up.
2. **Async enrich** — `/app` → Full (async) → submit → job polls until completed.
3. **Sync enrich** — Quick (sync) → tier1 disabled → submit → dossier returns once.
4. **Job detail** — `/app/jobs/{id}` loads on refresh; polls if still running.
5. **History** — `/app/history` lists jobs (requires backend `GET /enrich`).
6. **Opt-out** — `/opt-out` → submit → success message.
7. **Marketing** — `/`, `/recruiters`, … `/journalists` render; CTAs link to `/app?tiers=...`.
8. **Build** — `npm run build` and `npm run typecheck` pass.

## Architecture

- Browser calls `/api/*` only (BFF).
- `BACKEND_API_TOKEN` is server-only — never `NEXT_PUBLIC_*`.
- Field mapping lives in `src/lib/api-adapter.ts` only.
