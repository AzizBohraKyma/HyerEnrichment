"""Background enrichment task — adapter only; execution lives in Pipeline."""

from __future__ import annotations

import asyncio
import logging

from app.core.logging import set_job_id
from app.database.session import SessionLocal, engine
from app.enrichers.pipeline import Pipeline
from app.infrastructure.redis import close_redis
from app.modules.enrichment.job_events import close_events_redis
from app.observability.error_tracking import capture_exception, set_job_context

logger = logging.getLogger(__name__)


def run_enrichment_job(job_id: str) -> None:
    """RQ entrypoint (sync). Bridges into the async pipeline.

    RQ workers are synchronous, so each job gets its own event loop via
    asyncio.run and its own DB session. Never reuse a global loop here.
    """
    asyncio.run(_run_enrichment_job(job_id))


async def _run_enrichment_job(job_id: str) -> None:
    set_job_context(job_id)
    set_job_id(job_id)
    try:
        async with SessionLocal() as session:
            pipeline = Pipeline(session)
            await pipeline.execute_job(job_id)
    except Exception as exc:
        capture_exception(exc, tags={"job_id": job_id})
        raise
    finally:
        set_job_id(None)
        # Each job runs under asyncio.run with a fresh event loop, but the
        # Redis clients (both the shared request-path client and job_events'
        # dedicated pub/sub client) and the DB engine pool are module-global.
        # Connections created here are bound to this loop and break the next
        # job with "Event loop is closed" — drop them before the loop shuts
        # down. Missing close_events_redis() here previously left a stale
        # pub/sub client alive across jobs, which crashed the *next* job's
        # publish_job_status call once this loop closed (seen live during
        # the Tier 1 canary: job 2 in a worker process failed with
        # `AttributeError: 'NoneType' object has no attribute 'send'` /
        # `RuntimeError: Event loop is closed`).
        await close_redis()
        await close_events_redis()
        await engine.dispose()
