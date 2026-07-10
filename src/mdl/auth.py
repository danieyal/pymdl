"""Authentication helpers: password hashing, device ids, and pluggable token storage.

The app hashes the plaintext password with MD5 before sending it on the login/register/
email-change endpoints (spec §``authenticate``). A couple of endpoints
(``change_password``, ``deactivate``) send the plaintext instead — those are handled at
the call site, not here.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable


def md5_password(plaintext: str) -> str:
    """Return the lowercase hex MD5 digest the API expects for a password field."""
    return hashlib.md5(plaintext.encode("utf-8")).hexdigest()


def generate_device_id() -> str:
    """Generate a stable-looking device id. Callers should persist and reuse one value."""
    return uuid.uuid4().hex


@runtime_checkable
class TokenStore(Protocol):
    """Pluggable bearer-token storage.

    Implementations back the ``Authorization: Bearer <token>`` header. The client reads
    :meth:`get_token` before each authenticated request and calls :meth:`set_token` after
    a successful login, or :meth:`clear` on a 401.
    """

    def get_token(self) -> Optional[str]: ...

    def set_token(self, token: Optional[str]) -> None: ...

    def get_refresh_token(self) -> Optional[str]: ...

    def set_refresh_token(self, token: Optional[str]) -> None: ...

    def clear(self) -> None: ...


class InMemoryTokenStore:
    """Default token store. Holds tokens for the process lifetime only."""

    def __init__(
        self,
        token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        self._token = token
        self._refresh = refresh_token

    def get_token(self) -> Optional[str]:
        return self._token

    def set_token(self, token: Optional[str]) -> None:
        self._token = token

    def get_refresh_token(self) -> Optional[str]:
        return self._refresh

    def set_refresh_token(self, token: Optional[str]) -> None:
        self._refresh = token

    def clear(self) -> None:
        self._token = None
        self._refresh = None


class FileTokenStore:
    """Token store that persists to a small JSON file (e.g. ``~/.mydramalist/token.json``)."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data = self._load()

    def _load(self) -> dict[str, Optional[str]]:
        try:
            data: dict[str, Optional[str]] = json.loads(self._path.read_text("utf-8"))
        except (OSError, ValueError):
            return {}
        return data

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._data)
        # Write to a temp file created with owner-only permissions, then atomically
        # replace the target — avoids a TOCTOU window where the target file briefly
        # exists at the process umask before a chmod tightens it.
        fd = os.open(
            self._path.parent / f".{self._path.name}.tmp",
            os.O_CREAT | os.O_WRONLY | os.O_TRUNC,
            0o600,
        )
        try:
            os.write(fd, payload.encode("utf-8"))
        finally:
            os.close(fd)
        os.replace(
            self._path.parent / f".{self._path.name}.tmp",
            self._path,
        )

    def get_token(self) -> Optional[str]:
        return self._data.get("token")

    def set_token(self, token: Optional[str]) -> None:
        self._data["token"] = token
        self._save()

    def get_refresh_token(self) -> Optional[str]:
        return self._data.get("refresh_token")

    def set_refresh_token(self, token: Optional[str]) -> None:
        self._data["refresh_token"] = token
        self._save()

    def clear(self) -> None:
        self._data = {}
        self._save()
