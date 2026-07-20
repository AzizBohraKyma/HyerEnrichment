"""Sentry-compatible central error tracking (GlitchTip or Sentry SaaS).

No-op when ``SENTRY_DSN`` is unset — same opt-in pattern as Langfuse.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_initialized = False


def is_enabled() -> bool:
    return bool(get_settings().sentry_dsn.strip())


def init_error_tracking(settings: Settings | None = None) -> None:
    """Initialize the Sentry SDK once. Safe to call repeatedly."""
    global _initialized
    if _initialized:
        return

    cfg = settings if settings is not None else get_settings()
    dsn = cfg.sentry_dsn.strip()
    if not dsn:
        _initialized = True
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning("sentry-sdk not installed; error tracking disabled")
        _initialized = True
        return

    environment = cfg.sentry_environment.strip() or cfg.app_env
    release = cfg.sentry_release.strip() or None

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=cfg.sentry_traces_sample_rate,
        send_default_pii=cfg.sentry_send_default_pii,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
    )
    _initialized = True


def _attach_request(scope: Any, request: Request | None) -> None:
    if request is None:
        return
    scope.set_tag("http.method", request.method)
    scope.set_tag("http.path", request.url.path)


def capture_exception(
    exc: BaseException,
    *,
    request: Request | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Best-effort exception capture. No-op when unconfigured."""
    if not is_enabled():
        return
    try:
        import sentry_sdk
    except ImportError:
        return

    with sentry_sdk.push_scope() as scope:
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        _attach_request(scope, request)
        sentry_sdk.capture_exception(exc)


def set_job_context(job_id: str) -> None:
    """Attach enrichment job id to subsequent events in this worker task."""
    if not is_enabled():
        return
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.set_tag("job_id", job_id)


def flush_error_tracking(timeout: float = 2.0) -> None:
    """Flush pending events (for probes and worker shutdown)."""
    if not is_enabled():
        return
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.flush(timeout=timeout)
