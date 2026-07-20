#!/usr/bin/env python3
"""Run mypy against backend/app using the project virtualenv when present."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _python_executable() -> str:
    root = Path(__file__).resolve().parents[2]
    if sys.platform == "win32":
        candidate = root / "backend" / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = root / "backend" / ".venv" / "bin" / "python"
    if candidate.is_file():
        return str(candidate)
    return sys.executable


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    backend = root / "backend"
    result = subprocess.run(
        [_python_executable(), "-m", "mypy", "app"],
        cwd=backend,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
