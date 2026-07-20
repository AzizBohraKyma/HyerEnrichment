/**
 * Hyrepath Enrichment API load scenarios (k6).
 *
 * Env:
 *   BASE_URL      — API root (default http://api:8000 inside compose network)
 *   API_TOKEN     — Bearer token (default change-me)
 *   LOAD_PROFILE  — smoke | full (default smoke)
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const BASE_URL = (__ENV.BASE_URL || "http://api:8000").replace(/\/$/, "");
const API_TOKEN = __ENV.API_TOKEN || "change-me";
const PROFILE = (__ENV.LOAD_PROFILE || "smoke").toLowerCase();

const enrichEnqueueOk = new Rate("enrich_enqueue_ok");
const enrichJobCompleted = new Rate("enrich_job_completed");
const enrichSyncOk = new Rate("enrich_sync_ok");
const enrichJobsCompletedCount = new Counter("enrich_jobs_completed_count");
const enrichSyncOkCount = new Counter("enrich_sync_ok_count");
const jobCompleteMs = new Trend("enrich_job_complete_ms", true);
const pollCount = new Counter("enrich_poll_count");

// Smoke keeps async/sync at 1 VU: worker pipeline (~30–60s/job) is serial.
const PROFILES = {
  smoke: {
    readiness: { vus: 10, duration: "15s" },
    asyncEnrich: { vus: 1, duration: "2m" },
    syncEnrich: { vus: 1, duration: "2m" },
    pollDeadlineMs: 120000,
    syncTimeout: "120s",
  },
  full: {
    readiness: { vus: 50, duration: "1m" },
    asyncEnrich: { vus: 5, duration: "5m" },
    syncEnrich: { vus: 2, duration: "3m" },
    pollDeadlineMs: 180000,
    syncTimeout: "180s",
  },
};

const p = PROFILES[PROFILE] || PROFILES.smoke;

export const options = {
  scenarios: {
    readiness: {
      executor: "constant-vus",
      vus: p.readiness.vus,
      duration: p.readiness.duration,
      exec: "readiness",
      gracefulStop: "10s",
      tags: { scenario: "readiness" },
    },
    async_enrich: {
      executor: "constant-vus",
      vus: p.asyncEnrich.vus,
      duration: p.asyncEnrich.duration,
      exec: "asyncEnrich",
      startTime: p.readiness.duration,
      gracefulStop: "2m",
      tags: { scenario: "async_enrich" },
    },
    sync_enrich: {
      executor: "constant-vus",
      vus: p.syncEnrich.vus,
      duration: p.syncEnrich.duration,
      exec: "syncEnrich",
      startTime: addDuration(p.readiness.duration, p.asyncEnrich.duration),
      gracefulStop: "2m",
      tags: { scenario: "sync_enrich" },
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    "http_req_duration{endpoint:health}": ["p(95)<500"],
    "http_req_duration{endpoint:ready}": ["p(95)<800"],
    enrich_enqueue_ok: ["rate>0.95"],
    enrich_job_completed: ["rate>0.80"],
    enrich_jobs_completed_count: ["count>0"],
    enrich_sync_ok: ["rate>0.80"],
    enrich_sync_ok_count: ["count>0"],
    "http_req_duration{endpoint:enrich_sync}": ["p(95)<120000"],
  },
};

function addDuration(a, b) {
  return `${parseDurationSeconds(a) + parseDurationSeconds(b)}s`;
}

function parseDurationSeconds(d) {
  const m = String(d).match(/^(\d+)(s|m)$/);
  if (!m) return 0;
  const n = parseInt(m[1], 10);
  return m[2] === "m" ? n * 60 : n;
}

function authHeaders() {
  return {
    Authorization: `Bearer ${API_TOKEN}`,
    "Content-Type": "application/json",
  };
}

/** Unwrap shared success envelope or return body as-is. */
function unwrap(body) {
  if (body && typeof body === "object" && body.success === true && body.data != null) {
    return body.data;
  }
  return body;
}

export function readiness() {
  const health = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: "health" },
    timeout: "10s",
  });
  check(health, {
    "health status 200": (r) => r.status === 200,
    "health body ok": (r) => {
      try {
        const data = unwrap(r.json());
        return data && data.status === "ok";
      } catch (e) {
        return false;
      }
    },
  });

  const ready = http.get(`${BASE_URL}/ready`, {
    tags: { endpoint: "ready" },
    timeout: "15s",
  });
  check(ready, {
    "ready status 200": (r) => r.status === 200,
    "ready body ready": (r) => {
      try {
        const data = unwrap(r.json());
        return data && data.status === "ready";
      } catch (e) {
        return false;
      }
    },
  });

  sleep(0.2);
}

export function asyncEnrich() {
  const username = `load-async-${__VU}-${__ITER}-${Date.now()}`;
  const started = Date.now();
  let completed = false;

  const enqueue = http.post(
    `${BASE_URL}/enrich`,
    JSON.stringify({ username, requested_tiers: ["tier2"] }),
    { headers: authHeaders(), tags: { endpoint: "enrich_async" }, timeout: "30s" },
  );

  let jobId = null;
  const enqueued =
    enqueue.status === 202 &&
    (() => {
      try {
        const data = unwrap(enqueue.json());
        if (data && data.id && (data.status === "queued" || data.status === "running")) {
          jobId = data.id;
          return true;
        }
        return false;
      } catch (e) {
        return false;
      }
    })();

  enrichEnqueueOk.add(enqueued);
  check(enqueue, { "async enqueue 202": () => enqueued });

  if (!enqueued || !jobId) {
    enrichJobCompleted.add(false);
    sleep(1);
    return;
  }

  const deadline = Date.now() + p.pollDeadlineMs;
  let terminal = null;

  while (Date.now() < deadline) {
    const poll = http.get(`${BASE_URL}/enrich/${jobId}`, {
      headers: authHeaders(),
      tags: { endpoint: "enrich_poll" },
      timeout: "15s",
    });
    pollCount.add(1);
    if (poll.status !== 200) {
      sleep(2);
      continue;
    }
    try {
      const data = unwrap(poll.json());
      const st = data && data.status;
      if (st && st !== "queued" && st !== "running") {
        terminal = st;
        break;
      }
    } catch (e) {
      // keep polling
    }
    sleep(2);
  }

  completed = terminal === "completed";
  enrichJobCompleted.add(completed);
  if (completed) {
    enrichJobsCompletedCount.add(1);
    jobCompleteMs.add(Date.now() - started);
  }
  check(enqueue, { "async job completed": () => completed });
  sleep(1);
}

export function syncEnrich() {
  const username = `load-sync-${__VU}-${__ITER}-${Date.now()}`;
  const res = http.post(
    `${BASE_URL}/enrich/sync`,
    JSON.stringify({ username, requested_tiers: ["tier2"] }),
    {
      headers: authHeaders(),
      tags: { endpoint: "enrich_sync" },
      timeout: p.syncTimeout,
    },
  );

  const ok =
    res.status === 200 &&
    (() => {
      try {
        const data = unwrap(res.json());
        return !!(data && data.status && data.dossier);
      } catch (e) {
        return false;
      }
    })();

  enrichSyncOk.add(!!ok);
  if (ok) {
    enrichSyncOkCount.add(1);
  }
  check(res, { "sync enrich 200 + dossier": () => ok });
  sleep(1);
}
