"""CI guard: verify ``_sync`` matches what ``build_sync.py`` would generate.

Snapshots the committed ``_sync`` files, regenerates them from ``_async`` via unasync, and
diffs. Exits non-zero (listing the offending files) if any differ, so a contributor who
edited ``_async`` without regenerating is caught in CI.
"""

from __future__ import annotations

import os
import sys

import unasync

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_sync import ASYNC_DIR, REPLACEMENTS, SYNC_DIR, _iter_py_files  # noqa: E402


def _read(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main() -> int:
    # Snapshot current sync files.
    before = {p: _read(p) for p in _iter_py_files(SYNC_DIR.rstrip(os.sep))}

    # Regenerate in place.
    rule = unasync.Rule(fromdir=ASYNC_DIR, todir=SYNC_DIR, additional_replacements=REPLACEMENTS)
    unasync.unasync_files(_iter_py_files(ASYNC_DIR.rstrip(os.sep)), [rule])

    stale = [p for p in before if _read(p) != before[p]]
    # Also flag freshly-created files that weren't committed.
    for p in _iter_py_files(SYNC_DIR.rstrip(os.sep)):
        if p not in before:
            stale.append(p)

    if stale:
        print("_sync is out of date. Run: python scripts/build_sync.py")
        for p in sorted(stale):
            print(f"  {os.path.relpath(p)}")
        return 1
    print("_sync is up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
