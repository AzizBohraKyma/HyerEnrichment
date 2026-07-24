from redis import Redis
from rq import Queue

from app.core.config import get_settings
from app.domain.enums import RequestedTier

QUEUE_NAME = "enrichment"


def get_redis_connection() -> Redis:
    """Synchronous Redis connection for RQ (the async client is not compatible)."""
    return Redis.from_url(get_settings().redis_url)


def get_queue_name_for_tiers(requested_tiers: list[RequestedTier]) -> str:
    """Determine which queue to use based on requested tiers."""
    settings = get_settings()

    if settings.worker_queue_mode == "single":
        return "enrichment"

    # Per-tier routing: tier1 jobs go to tier1 queue, everything else to tier234
    if RequestedTier.tier1 in requested_tiers:
        return "tier1"
    return "tier234"


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis_connection())


def get_worker_queue() -> Queue:
    """Get the queue this worker should listen to."""
    settings = get_settings()

    if settings.worker_queue_mode == "single":
        queue_name = "enrichment"
    else:
        # In per_tier mode, worker must specify which queue to listen to
        if not settings.worker_target_queue:
            raise ValueError("WORKER_TARGET_QUEUE required when WORKER_QUEUE_MODE=per_tier")
        queue_name = settings.worker_target_queue

    return Queue(queue_name, connection=get_redis_connection())


def enqueue_enrichment(job_id: str, requested_tiers: list[RequestedTier] | None = None) -> None:
    """Enqueue an enrichment job to the appropriate tier-based queue."""
    from app.workers.jobs import run_enrichment_job

    # Default to all tiers if none specified (backward compatibility)
    tiers = requested_tiers if requested_tiers is not None else list(RequestedTier)
    queue_name = get_queue_name_for_tiers(tiers)
    connection = get_redis_connection()
    queue = Queue(queue_name, connection=connection)
    queue.enqueue(run_enrichment_job, job_id)
