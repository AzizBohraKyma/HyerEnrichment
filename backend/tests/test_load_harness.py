"""Contract tests for the k6 load-test harness (no Docker required)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
K6_MAIN = BACKEND / "load" / "k6" / "main.js"
LOADTEST_COMPOSE = BACKEND / "docker" / "docker-compose.loadtest.yml"
RUNNER = BACKEND / "scripts" / "run_load_test.py"
MAKEFILE = REPO_ROOT / "Makefile"
REPORT_NAME = "load-report.json"


def test_load_harness_files_exist() -> None:
    assert K6_MAIN.is_file(), f"missing {K6_MAIN}"
    assert LOADTEST_COMPOSE.is_file(), f"missing {LOADTEST_COMPOSE}"
    assert RUNNER.is_file(), f"missing {RUNNER}"
    assert MAKEFILE.is_file(), f"missing {MAKEFILE}"


def test_makefile_has_load_test_target() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"(?m)^load-test:", text), "Makefile missing load-test target"
    assert "run_load_test.py" in text
    help_block = text.split("help:")[1].split("setup:")[0]
    assert "load-test" in help_block


def test_k6_script_has_thresholds_and_endpoints() -> None:
    src = K6_MAIN.read_text(encoding="utf-8")
    assert "thresholds" in src
    assert "/health" in src
    assert "/ready" in src
    assert "/enrich" in src
    assert "/enrich/sync" in src
    assert "LOAD_PROFILE" in src
    assert "enrich_enqueue_ok" in src
    assert "enrich_job_completed" in src
    assert "enrich_jobs_completed_count" in src
    assert "enrich_sync_ok_count" in src


def test_loadtest_compose_elevates_rate_limits() -> None:
    raw = LOADTEST_COMPOSE.read_text(encoding="utf-8")
    async_match = re.search(
        r'MAX_ASYNC_REQUESTS_PER_MINUTE:\s*"?(\d+)"?',
        raw,
    )
    sync_match = re.search(
        r'MAX_SYNC_REQUESTS_PER_MINUTE:\s*"?(\d+)"?',
        raw,
    )
    assert async_match, "MAX_ASYNC_REQUESTS_PER_MINUTE missing from loadtest compose"
    assert sync_match, "MAX_SYNC_REQUESTS_PER_MINUTE missing from loadtest compose"
    async_limit = int(async_match.group(1))
    sync_limit = int(sync_match.group(1))
    assert async_limit >= 1000, f"expected elevated async limit, got {async_limit}"
    assert sync_limit >= 1000, f"expected elevated sync limit, got {sync_limit}"
    assert async_limit > 30
    assert sync_limit > 10


def test_runner_writes_load_report_path() -> None:
    src = RUNNER.read_text(encoding="utf-8")
    assert REPORT_NAME in src
    assert ".e2e-results" in src
    assert "grafana/k6" in src or "K6_IMAGE" in src
    assert "docker-compose.loadtest.yml" in src
    assert "docker-compose.fake-sidecars.yml" in src
