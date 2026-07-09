"""Generate the synchronous package (``mdl._sync``) from the async source.

The async implementation under ``src/mdl/_async`` is the single source of truth.
This script runs ``unasync`` to mechanically strip ``await`` / ``async`` and swap the
async-only names for their sync equivalents, writing the result into
``src/mdl/_sync``. Re-run it whenever the async source changes; CI checks that the
committed ``_sync`` tree matches the generated output.
"""

from __future__ import annotations

import os
import sys

import unasync

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASYNC_DIR = os.path.join(ROOT, "src", "mdl", "_async") + os.sep
SYNC_DIR = os.path.join(ROOT, "src", "mdl", "_sync") + os.sep

REPLACEMENTS = {
    "AsyncClient": "Client",  # httpx.AsyncClient -> httpx.Client
    "AsyncSession": "Session",  # curl_cffi.requests.AsyncSession -> Session
    "AsyncTransport": "SyncTransport",
    "AsyncResource": "Resource",
    "aclose": "close",
    "__aenter__": "__enter__",
    "__aexit__": "__exit__",
}


def _iter_py_files(base: str) -> list[str]:
    out: list[str] = []
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".py"):
                out.append(os.path.join(dirpath, name))
    return out


def main() -> int:
    rule = unasync.Rule(
        fromdir=ASYNC_DIR,
        todir=SYNC_DIR,
        additional_replacements=REPLACEMENTS,
    )
    files = _iter_py_files(ASYNC_DIR.rstrip(os.sep))
    unasync.unasync_files(files, [rule])
    print(f"Generated {len(files)} file(s) into {SYNC_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
