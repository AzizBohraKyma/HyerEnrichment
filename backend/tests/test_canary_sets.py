"""Shape/unit tests for committed 20-row canary example JSON files."""

from __future__ import annotations

import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
TIER1_EXAMPLE = BACKEND / "docs" / "tier1_canary_set.example.json"
TIER234_EXAMPLE = BACKEND / "docs" / "tier234_canary_set.example.json"

TIER1_CATEGORIES = {"technical", "non-technical", "private"}
TIER234_CATEGORIES = {"technical", "non-technical", "sparse"}
TIER234_ENRICHER_SLUGS = {
    "sherlock",
    "maigret",
    "social_analyzer",
    "gitrecon",
    "theharvester",
    "email_discover",
    "email_verify",
    "crosslinked",
    "jobspy",
    "local_business",
}
PUBLIC_IDENTIFIERS = {
    "torvalds",
    "satyanadella",
    "Microsoft",
    "noreply@github.com",
    "coffee shop San Francisco",
    "software engineer remote",
}


def _load_array(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    return raw


def test_tier1_example_has_twenty_rows_with_schema() -> None:
    entries = _load_array(TIER1_EXAMPLE)
    assert len(entries) == 20
    counts = {cat: 0 for cat in TIER1_CATEGORIES}
    for entry in entries:
        assert entry.get("slug")
        assert str(entry.get("linkedin_url", "")).startswith("https://www.linkedin.com/in/")
        category = entry.get("category")
        assert category in TIER1_CATEGORIES
        counts[category] += 1
        if category == "private":
            assert entry.get("expect_photo") is False
        else:
            assert entry.get("expect_photo") is True
        assert "your-" in entry["slug"]
    assert counts["technical"] == 7
    assert counts["non-technical"] == 7
    assert counts["private"] == 6


def test_tier234_example_has_twenty_rows_with_public_identifiers() -> None:
    entries = _load_array(TIER234_EXAMPLE)
    assert len(entries) == 20
    seen_ids: set[str] = set()
    used_public = False
    for entry in entries:
        entry_id = entry.get("id")
        assert entry_id and entry_id not in seen_ids
        seen_ids.add(entry_id)
        assert entry.get("category") in TIER234_CATEGORIES
        enrichers = entry.get("enrichers")
        assert isinstance(enrichers, list) and enrichers
        assert set(enrichers).issubset(TIER234_ENRICHER_SLUGS)
        blob = json.dumps(entry)
        if any(token in blob for token in PUBLIC_IDENTIFIERS):
            used_public = True
    assert used_public
