from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.config import get_settings

_redis: Redis | None = None


def get_redis_client() -> Redis:
    """Return the shared async Redis client, creating it on first use.

    Connections are established lazily by redis-py on the first command,
    so importing or calling this does not require a live Redis server.
    """
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dependency yielding the shared Redis client."""
    yield get_redis_client()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
