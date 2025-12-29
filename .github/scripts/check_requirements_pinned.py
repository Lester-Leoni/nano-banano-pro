#!/usr/bin/env python3
"""Fail CI if requirements.txt contains unpinned dependencies.

Goal: predictable installs for an open-source release.
We only allow exact pins (==) for package specifiers.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


PIN_RE = re.compile(r"^[A-Za-z0-9_.-]+(\[[^\]]+\])?==[^=]+$")


def is_relevant_line(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#"):
        return False
    # pip options / includes are allowed, but should be used intentionally.
    if s.startswith(("-r ", "--requirement", "--index-url", "--extra-index-url", "--trusted-host")):
        return False
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check_requirements_pinned.py <requirements.txt>", file=sys.stderr)
        return 2

    req_path = Path(sys.argv[1])
    if not req_path.exists():
        print(f"requirements file not found: {req_path}", file=sys.stderr)
        return 2

    bad: list[tuple[int, str]] = []
    for i, line in enumerate(req_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not is_relevant_line(line):
            continue
        s = line.strip()
        if not PIN_RE.match(s):
            bad.append((i, s))

    if bad:
        print("Found unpinned or unsupported requirement specifiers:", file=sys.stderr)
        for i, s in bad:
            print(f"  L{i}: {s}", file=sys.stderr)
        print("\nExpected exact pins, e.g.: package==1.2.3", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
