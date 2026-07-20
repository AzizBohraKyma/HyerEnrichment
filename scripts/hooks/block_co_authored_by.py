#!/usr/bin/env python3
"""Reject commit messages that include Co-authored-by trailers."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("ERROR: commit message file path required", file=sys.stderr)
        return 1

    message = Path(sys.argv[1]).read_text(encoding="utf-8")
    if "co-authored-by:" in message.lower():
        print("ERROR: Co-authored-by trailers are not allowed in commit messages", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
