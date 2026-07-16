"""Unit tests for run_canary_score ops runner (no live probes)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND / "scripts" / "run_canary_score.py"


def _load_runner():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    spec = importlib.util.spec_from_file_location("run_canary_score", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_canary_score"] = mod
    spec.loader.exec_module(mod)
    return mod


runner = _load_runner()


def test_help_exits_zero() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=str(BACKEND),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "canary" in completed.stdout.lower()


def test_build_parser_defaults() -> None:
    args = runner.build_parser().parse_args([])
    assert args.tier == "all"
    assert args.dry_run is False


def test_tier1_local_filled_detects_placeholders(tmp_path: Path) -> None:
    placeholders = tmp_path / "tier1.json"
    placeholders.write_text(
        json.dumps(
            [{"slug": "your-tech-slug-01", "linkedin_url": "https://www.linkedin.com/in/your-tech-slug-01"}]
        ),
        encoding="utf-8",
    )
    assert runner.tier1_local_filled(placeholders) is False

    real = tmp_path / "real.json"
    real.write_text(
        json.dumps(
            [{"slug": "public-profile", "linkedin_url": "https://www.linkedin.com/in/public-profile"}]
        ),
        encoding="utf-8",
    )
    assert runner.tier1_local_filled(real) is True


def test_ensure_canary_file_copies_when_missing(tmp_path: Path) -> None:
    example = tmp_path / "example.json"
    local = tmp_path / "local.json"
    example.write_text("[]", encoding="utf-8")
    action = runner.ensure_canary_file(example, local, dry_run=False)
    assert action == "copied"
    assert local.read_text(encoding="utf-8") == "[]"


def test_ensure_canary_file_dry_run_does_not_copy(tmp_path: Path) -> None:
    example = tmp_path / "example.json"
    local = tmp_path / "local.json"
    example.write_text("[]", encoding="utf-8")
    action = runner.ensure_canary_file(example, local, dry_run=True)
    assert action == "would_copy"
    assert not local.exists()


def test_dry_run_main_prints_plan(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["run_canary_score.py", "--dry-run", "--tier", "tier234"])
    assert runner.main() == 0
    captured = capsys.readouterr()
    assert "Dry run complete" in captured.out
    assert "tier234" in captured.out
