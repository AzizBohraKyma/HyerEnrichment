from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.redis import close_redis, get_redis_client
from app.observability.error_tracking import init_error_tracking


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_error_tracking()
    get_redis_client()
    yield
    await close_redis()
