import logging
from collections.abc import AsyncIterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
# pool_pre_ping recycles stale connections (e.g. after a Postgres restart).
engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
logger.info("database engine created (dialect=%s)", engine.dialect.name)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
BASELINE_REVISION = "001_baseline_schema"


def alembic_config(database_url: str | None = None) -> Config:
    """Build Alembic Config with package-relative paths (Docker + local safe)."""
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url or settings.database_url)
    return cfg


def _to_sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return url


def legacy_pre_alembic(connection) -> bool:
    """True when ORM tables exist but Alembic has never stamped this database."""
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    return "jobs" in tables and "alembic_version" not in tables


def run_migrations(database_url: str, *, stamp_if_legacy: bool = True) -> None:
    """Stamp legacy bootstrap DBs at baseline (optional), then upgrade to head.

    For Postgres, prefer calling via ``init_db`` or an async check when no
    sync DBAPI (psycopg) is installed — this helper uses a sync URL rewrite
    and may fail on Postgres without psycopg. SQLite always works.
    """
    cfg = alembic_config(database_url)
    if stamp_if_legacy:
        sync_engine = create_engine(_to_sync_url(database_url))
        try:
            with sync_engine.connect() as conn:
                needs_stamp = legacy_pre_alembic(conn)
        finally:
            sync_engine.dispose()
        if needs_stamp:
            logger.info("pre-Alembic schema detected; stamping %s", BASELINE_REVISION)
            command.stamp(cfg, BASELINE_REVISION)
    command.upgrade(cfg, "head")


async def init_db() -> None:
    """Apply Alembic migrations. Auto-stamps legacy unversioned databases."""
    cfg = alembic_config()

    async with engine.begin() as conn:
        needs_stamp = await conn.run_sync(legacy_pre_alembic)

    if needs_stamp:
        logger.info("pre-Alembic schema detected; stamping %s", BASELINE_REVISION)
        command.stamp(cfg, BASELINE_REVISION)

    command.upgrade(cfg, "head")
    logger.info("database schema migrated to alembic head (dialect=%s)", engine.dialect.name)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
