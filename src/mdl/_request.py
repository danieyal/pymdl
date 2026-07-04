"""Pure request construction — no I/O, shared by both the sync and async transports.

Reproduces ``CustomHttpClient._buildHeaders`` / ``_mergeHeaders`` (spec §2): every request
carries ``mdl-api-key`` and ``version``; ``Content-Type: application/json`` is sent unless
the request is multipart; ``Authorization: Bearer`` is attached when a token is present and
the endpoint needs auth; ``Accept-Language`` is sent when a lang code is configured.

Everything here is a plain function/dataclass so it can be unit-tested without a network
and reused verbatim by the async source and its unasync-generated sync twin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from .config import ClientConfig


@dataclass
class PreparedRequest:
    """A fully-described HTTP call, independent of the transport that will execute it.

    ``path`` may be relative to the API base URL or an absolute ``http(s)://`` URL
    (used for the multipart upload endpoint). ``auth`` marks whether a bearer token
    should be attached. ``multipart`` swaps JSON encoding for form-data and strips the
    JSON ``Content-Type`` (mirrors ``stripContentType``).
    """

    method: str
    path: str
    params: Optional[dict[str, Any]] = None
    json: Any = None
    data: Optional[dict[str, Any]] = None
    files: Optional[dict[str, Any]] = None
    auth: bool = True
    multipart: bool = False

    def url(self, base_url: str) -> str:
        if self.path.startswith("http://") or self.path.startswith("https://"):
            return self.path
        return f"{base_url}{self.path}"


@dataclass
class TransportResponse:
    """Transport-agnostic result of an executed request."""

    status_code: int
    json: Any
    text: str
    headers: Mapping[str, str]
    url: str


def build_headers(
    config: ClientConfig,
    token: Optional[str],
    *,
    auth: bool = True,
    multipart: bool = False,
    extra: Optional[Mapping[str, str]] = None,
) -> dict[str, str]:
    """Assemble the header set for a request (see module docstring)."""
    headers: dict[str, str] = {
        "mdl-api-key": config.api_key,
        "version": config.app_version,
    }
    if not multipart:
        headers["Content-Type"] = "application/json"
    if auth and token:
        headers["Authorization"] = f"Bearer {token}"
    if config.lang_code:
        headers["Accept-Language"] = config.lang_code
    if extra:
        headers.update(extra)
    return headers


def clean_params(params: Optional[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
    """Drop ``None`` values and coerce bools to the app's ``1`` convention.

    Query flags such as ``expand=1`` / ``edge=1`` are integers on the wire; passing a
    Python ``True`` should serialize the same way.
    """
    if not params:
        return None
    out: dict[str, Any] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = 1 if value else 0
        else:
            out[key] = value
    return out or None


def extract_error_message(body: Any) -> str:
    """Pull a human message out of an error body's ``message`` / ``error`` key."""
    if isinstance(body, Mapping):
        for key in ("message", "error"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
    if isinstance(body, str) and body:
        return body
    return "request failed"


@dataclass
class _Unset:
    """Sentinel so callers can distinguish 'omit' from 'explicit null' in bodies."""

    _singleton: bool = field(default=True, repr=False)


UNSET = _Unset()


def compact(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """Return a dict with ``UNSET`` values removed (keeps explicit ``None``)."""
    return {k: v for k, v in mapping.items() if v is not UNSET}
