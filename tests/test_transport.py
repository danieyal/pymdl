"""Transport ownership/close lifecycle for the default curl_cffi backend.

The other suites inject an httpx client (so respx can mock the network), which means the
real curl_cffi branch of the transport — session construction with ``impersonate`` and the
owned-session close lifecycle — is otherwise never exercised. These tests patch the
``Session`` / ``AsyncSession`` symbols so no live request is made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from mdl._async._transport import AsyncTransport
from mdl._sync._transport import SyncTransport
from mdl.config import ClientConfig

# --- sync ----------------------------------------------------------------

def test_sync_transport_builds_curl_session_with_impersonate() -> None:
    config = ClientConfig(api_key="k", impersonate="safari_ios", timeout=12.0)
    fake_session = MagicMock()
    with patch("mdl._sync._transport.Session", return_value=fake_session) as session_cls:
        transport = SyncTransport(config)
        session_cls.assert_called_once_with(timeout=12.0, impersonate="safari_ios")
        assert transport._owns_client is True
        transport.close()
        fake_session.close.assert_called_once()


def test_sync_transport_injected_client_is_not_owned_or_closed() -> None:
    injected = MagicMock()
    with patch("mdl._sync._transport.Session") as session_cls:
        transport = SyncTransport(ClientConfig(api_key="k"), client=injected)
        session_cls.assert_not_called()  # no curl_cffi session created
        assert transport._owns_client is False
        transport.close()
        injected.close.assert_not_called()  # caller owns the injected client


# --- async ---------------------------------------------------------------

async def test_async_transport_builds_curl_session_with_impersonate() -> None:
    config = ClientConfig(api_key="k", impersonate="chrome131", timeout=7.0)
    fake_session = MagicMock()
    fake_session.close = AsyncMock()
    with patch(
        "mdl._async._transport.AsyncSession", return_value=fake_session
    ) as session_cls:
        transport = AsyncTransport(config)
        session_cls.assert_called_once_with(timeout=7.0, impersonate="chrome131")
        assert transport._owns_client is True
        await transport.aclose()
        fake_session.close.assert_awaited_once()


async def test_async_transport_injected_client_is_not_owned_or_closed() -> None:
    injected = MagicMock()
    injected.close = AsyncMock()
    with patch("mdl._async._transport.AsyncSession") as session_cls:
        transport = AsyncTransport(ClientConfig(api_key="k"), client=injected)
        session_cls.assert_not_called()
        assert transport._owns_client is False
        await transport.aclose()
        injected.close.assert_not_awaited()


# --- header case-insensitivity ---------------------------------------------
#
# respx/httpx lowercases header keys on Response construction, so the respx
# suites can't exercise the case-mismatch path. curl_cffi (the production
# transport) preserves the on-the-wire casing the server used, which commonly
# differs from the lowercase ``PAGINATION_TOTAL_HEADER`` constant. _process
# must normalize so the (lowercase) constant matches regardless of wire casing.


class _FakeResponse:
    """Minimal response stand-in preserving original header casing (like curl_cffi)."""

    def __init__(self, *, status_code: int, text: str, headers: dict[str, str]) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers


def test_sync_transport_normalizes_mixed_case_headers() -> None:
    transport = SyncTransport(ClientConfig(api_key="k"), client=MagicMock())
    fake = _FakeResponse(
        status_code=200, text="[]", headers={"X-Pagination-Total": "9", "Content-Type": "x"}
    )
    resp = transport._process(fake, "https://example/v1/titles/1/comments")
    # keys are lowercased…
    assert set(resp.headers) == {"x-pagination-total", "content-type"}
    # …so the lowercase lookup constant used by _page() matches.
    assert resp.headers.get("x-pagination-total") == "9"


async def test_async_transport_normalizes_mixed_case_headers() -> None:
    transport = AsyncTransport(ClientConfig(api_key="k"), client=MagicMock())
    fake = _FakeResponse(
        status_code=200, text="[]", headers={"X-Pagination-Total": "9", "Content-Type": "x"}
    )
    resp = transport._process(fake, "https://example/v1/titles/1/comments")
    assert set(resp.headers) == {"x-pagination-total", "content-type"}
    assert resp.headers.get("x-pagination-total") == "9"
