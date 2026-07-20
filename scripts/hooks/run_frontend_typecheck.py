#!/usr/bin/env python3
"""Run frontend TypeScript typecheck."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    frontend = root / "frontend"
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run([npm, "run", "typecheck"], cwd=frontend, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
