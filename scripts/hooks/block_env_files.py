#!/usr/bin/env python3
"""Fail if staged files include real .env or .env.local secrets."""

from __future__ import annotations

import re
import subprocess
import sys

ENV_PATTERN = re.compile(r"(^|/)\.env$|\.env\.local$")


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr or "ERROR: unable to read staged files", file=sys.stderr)
        return result.returncode

    blocked = [line for line in result.stdout.splitlines() if ENV_PATTERN.search(line)]
    if not blocked:
        return 0

    print("ERROR: refusing to commit .env or .env.local file", file=sys.stderr)
    print("Use .env.example for templates. Real secrets belong in ignored local files.", file=sys.stderr)
    for path in blocked:
        print(f"  - {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
