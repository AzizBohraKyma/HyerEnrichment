from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status

from app.config import get_settings
from app.providers.notify import notify_change_signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _parse_changedetection_payload(
    payload: dict[str, Any],
) -> tuple[str, str, str, str | None]:
    """Extract non-PII watch metadata from a changedetection.io webhook body."""
    watch_id = str(
        payload.get("watch_uuid") or payload.get("uuid") or payload.get("watch_id") or "unknown"
    )
    title = str(payload.get("watch_title") or payload.get("title") or "unknown")
    url = str(payload.get("watch_url") or payload.get("url") or payload.get("link") or "")
    raw_ts = payload.get("timestamp") or payload.get("last_changed")
    timestamp = str(raw_ts) if raw_ts is not None else None
    return watch_id, title, url, timestamp


@router.post("/changedetection", status_code=status.HTTP_202_ACCEPTED)
async def changedetection_webhook(
    payload: dict[str, Any],
    x_signal_token: str | None = Header(default=None),
) -> dict[str, str]:
    """Consume changedetection.io change notifications.

    Unauthenticated by design (external self-hosted watcher posts here), but an
    optional shared secret can be required via CHANGEDETECTION_API_KEY. Only
    non-PII fields (watch id/title/url of the monitored page) are logged or
    forwarded to NOTIFY_WEBHOOK_URL.
    """
    settings = get_settings()
    expected = settings.changedetection_api_key.strip()
    if expected and x_signal_token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signal token")

    watch_id, title, url, timestamp = _parse_changedetection_payload(payload)

    logger.info(
        "changedetection signal received: watch=%s title=%s",
        watch_id,
        title,
    )
    await notify_change_signal(
        watch_id=watch_id,
        title=title,
        url=url,
        timestamp=timestamp,
    )
    return {"status": "accepted"}
