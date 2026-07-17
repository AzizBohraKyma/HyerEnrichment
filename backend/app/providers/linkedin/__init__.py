"""LinkedIn profile photo scraping via Selenium + Multilogin.

Selenium-backed modules load lazily so ``from app.providers.linkedin.urls
import extract_linkedin_slug`` (used by LinkedInPhotoEnricher and host unit
tests) does not require the ``selenium`` package.
"""

from __future__ import annotations

from typing import Any

from app.providers.linkedin.types import (
    ExtractionMethod,
    LinkedInPhotoError,
    LinkedInPhotoResult,
    NO_RETRY_OUTCOMES,
    ROTATE_PROFILE_OUTCOMES,
)
from app.providers.linkedin.urls import (
    extract_linkedin_slug,
    is_placeholder_image_url,
    placeholder_fragments,
    photo_url_from_srcset,
)

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "LinkedInBrowserClient": ("app.providers.linkedin.client", "LinkedInBrowserClient"),
    "scrape_photo": ("app.providers.linkedin.client", "scrape_photo"),
    "connect_selenium": ("app.providers.linkedin.login", "connect_selenium"),
    "detect_page_state": ("app.providers.linkedin.login", "detect_page_state"),
    "has_valid_linkedin_session": ("app.providers.linkedin.login", "has_valid_linkedin_session"),
    "login_linkedin": ("app.providers.linkedin.login", "login_linkedin"),
    "extract_photo_url": ("app.providers.linkedin.photo", "extract_photo_url"),
    "save_failure_screenshot": ("app.providers.linkedin.photo", "save_failure_screenshot"),
    "download_image": ("app.providers.linkedin.scrape", "download_image"),
    "scrape_on_driver": ("app.providers.linkedin.scrape", "scrape_on_driver"),
}

__all__ = [
    "ExtractionMethod",
    "LinkedInBrowserClient",
    "LinkedInPhotoError",
    "LinkedInPhotoResult",
    "NO_RETRY_OUTCOMES",
    "ROTATE_PROFILE_OUTCOMES",
    "connect_selenium",
    "detect_page_state",
    "download_image",
    "extract_linkedin_slug",
    "extract_photo_url",
    "has_valid_linkedin_session",
    "is_placeholder_image_url",
    "login_linkedin",
    "photo_url_from_srcset",
    "placeholder_fragments",
    "save_failure_screenshot",
    "scrape_on_driver",
    "scrape_photo",
]


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr = target
    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, attr)
    globals()[name] = value
    return value
