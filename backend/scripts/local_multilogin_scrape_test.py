"""Local Multilogin LinkedIn photo scrape (no Docker).

Checks the Multilogin launcher on the host, scrapes a profile photo via the
same LinkedInBrowserClient path as the worker, and writes the image under
backend/artifacts/tier1/.

Prerequisites:
  - Multilogin X running on Windows (port 45001)
  - backend/.env with MULTILOGIN_* and LINKEDIN_BOT_* filled
  - MULTILOGIN_SELENIUM_HOST=http://127.0.0.1 (host-native; not host.docker.internal)
  - pip install -e ".[enrichers]" in a venv

Usage (from backend/):
  python scripts/local_multilogin_scrape_test.py
  python scripts/local_multilogin_scrape_test.py --linkedin-url https://www.linkedin.com/in/someone/
  python scripts/local_multilogin_scrape_test.py --launcher-only
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.providers.linkedin.urls import extract_linkedin_slug
from app.providers.linkedin_browser import LinkedInBrowserClient, LinkedInPhotoError

DEFAULT_URL = "https://www.linkedin.com/in/rajshamani/?isSelfProfile=false"
OUT_DIR = ROOT / "artifacts" / "tier1"


def _launcher_base(settings) -> str:
    return settings.multilogin_launcher_url.rstrip("/")


async def check_launcher(settings) -> int:
    """Return 0 if Multilogin launcher answers on the configured URL."""
    base = _launcher_base(settings)
    url = f"{base}/"
    print(f"Checking launcher: {url}")
    print(f"Selenium host:     {settings.multilogin_selenium_host}")
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            response = await client.get(url)
        # Launcher often returns 404 on bare /api/v2/ — that still means it is up.
        print(f"Launcher HTTP {response.status_code} (up)")
        return 0
    except httpx.HTTPError as exc:
        print(f"Launcher unreachable: {exc}")
        print("Start Multilogin X on Windows and retry (PowerShell: curl.exe -sk https://127.0.0.1:45001/api/v2/).")
        return 1


def _extension(content_type: str | None) -> str:
    normalized = (content_type or "image/jpeg").split(";")[0].strip().lower()
    return {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }.get(normalized, "jpg")


async def scrape_and_save(*, linkedin_url: str) -> int:
    settings = get_settings()
    if not settings.enable_tier1:
        print("WARN: ENABLE_TIER1 is false in .env — scrape client still runs, but production worker would skip Tier 1.")
    if settings.browser_mode.strip().lower() != "multilogin":
        print(f"WARN: BROWSER_MODE={settings.browser_mode!r} (expected multilogin).")

    if await check_launcher(settings) != 0:
        return 1

    slug = extract_linkedin_slug(linkedin_url) or "profile"
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", slug)[:64]
    print(f"Scraping {linkedin_url} (slug={slug})...")

    client = LinkedInBrowserClient()
    result = await client.scrape_photo(linkedin_url, job_id=f"local-{slug}")
    if result.outcome != LinkedInPhotoError.SUCCESS or not result.image_bytes:
        print(f"Scrape failed: outcome={result.outcome}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ext = _extension(result.content_type)
    out = OUT_DIR / f"local_mlx_{slug}_{stamp}.{ext}"
    out.write_bytes(result.image_bytes)

    print(f"OK: {len(result.image_bytes)} bytes")
    print(f"  method={result.method} confidence={result.confidence}")
    print(f"  content_type={result.content_type}")
    print(f"  saved={out}")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="Local Multilogin LinkedIn photo scrape")
    parser.add_argument(
        "--linkedin-url",
        default=DEFAULT_URL,
        help="LinkedIn /in/{slug} URL to scrape",
    )
    parser.add_argument(
        "--launcher-only",
        action="store_true",
        help="Only check Multilogin launcher reachability",
    )
    args = parser.parse_args()

    settings = get_settings()
    if args.launcher_only:
        return await check_launcher(settings)
    return await scrape_and_save(linkedin_url=args.linkedin_url)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
