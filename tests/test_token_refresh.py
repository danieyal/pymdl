"""Token refresh: explicit ``auth.refresh()`` and the transport's refresh-and-retry on 401."""

from __future__ import annotations

import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
import respx
from httpx import Response
from tests.conftest import API_KEY, BASE_URL

from mdl import AsyncMDLClient, MDLClient
from mdl.errors import MDLAuthError, MDLConfigError

NEW_PAIR = {
    "access_token": "new",
    "refresh_token": "R2",
    "expires_in": 2592000,
    "token_type": "Bearer",
}
# The OAuth2 server reports a rejected refresh token with HTTP 200 and a text/plain body.
INVALID_GRANT = Response(
    200,
    text=json.dumps(
        {
            "error": "invalid_grant",
            "error_description": "The provided authorization grant is invalid.",
        }
    ),
    headers={"Content-Type": "text/plain; charset=UTF-8"},
)
EXPIRED = Response(401, json={"code": 401, "message": "Invalid access token."})


def _settings_by_token(request: Any) -> Response:
    if request.headers.get("Authorization") == "Bearer new":
        return Response(200, json={"username": "alice"})
    return EXPIRED


@respx.mock
def test_401_refreshes_and_retries(sync_client) -> None:
    sync_client.tokens.set_token("old")
    sync_client.tokens.set_refresh_token("R1")
    settings = respx.get(f"{BASE_URL}/users/settings").mock(side_effect=_settings_by_token)
    refresh = respx.post(f"{BASE_URL}/auth/refresh").mock(
        return_value=Response(200, json=NEW_PAIR)
    )

    profile = sync_client.account.get_profile()

    assert profile.username == "alice"
    assert settings.call_count == 2
    assert sync_client.tokens.get_token() == "new"
    assert sync_client.tokens.get_refresh_token() == "R2"
    refresh_request = refresh.calls.last.request
    assert json.loads(refresh_request.content) == {"refresh_token": "R1"}
    assert "Authorization" not in refresh_request.headers


@respx.mock
def test_rejected_refresh_clears_tokens_and_raises(sync_client) -> None:
    sync_client.tokens.set_token("old")
    sync_client.tokens.set_refresh_token("R1")
    settings = respx.get(f"{BASE_URL}/users/settings").mock(return_value=EXPIRED)
    respx.post(f"{BASE_URL}/auth/refresh").mock(return_value=INVALID_GRANT)

    with pytest.raises(MDLAuthError) as excinfo:
        sync_client.account.get_profile()

    assert excinfo.value.status_code == 401
    assert settings.call_count == 1
    assert sync_client.tokens.get_token() is None
    assert sync_client.tokens.get_refresh_token() is None


@respx.mock
def test_retry_rejected_again_does_not_loop(sync_client) -> None:
    sync_client.tokens.set_token("old")
    sync_client.tokens.set_refresh_token("R1")
    settings = respx.get(f"{BASE_URL}/users/settings").mock(return_value=EXPIRED)
    refresh = respx.post(f"{BASE_URL}/auth/refresh").mock(
        return_value=Response(200, json=NEW_PAIR)
    )

    with pytest.raises(MDLAuthError):
        sync_client.account.get_profile()

    assert settings.call_count == 2
    assert refresh.call_count == 1
    assert sync_client.tokens.get_token() is None


@respx.mock
def test_anonymous_401_does_not_refresh(sync_client) -> None:
    sync_client.tokens.set_refresh_token("R1")
    respx.post(url__regex=rf"{BASE_URL}/auth/login.*").mock(return_value=EXPIRED)
    refresh = respx.post(f"{BASE_URL}/auth/refresh").mock(
        return_value=Response(200, json=NEW_PAIR)
    )

    with pytest.raises(MDLAuthError):
        sync_client.auth.login("alice", "pw", device_id="d")

    assert not refresh.called
    # The request carried no token, so the stored ones are not stale.
    assert sync_client.tokens.get_refresh_token() == "R1"


@respx.mock
def test_explicit_refresh_stores_new_pair(sync_client) -> None:
    sync_client.tokens.set_refresh_token("R1")
    respx.post(f"{BASE_URL}/auth/refresh").mock(return_value=Response(200, json=NEW_PAIR))

    auth = sync_client.auth.refresh()

    assert auth.access_token == "new"
    assert auth.expires_in == 2592000
    assert sync_client.tokens.get_token() == "new"
    assert sync_client.tokens.get_refresh_token() == "R2"


@respx.mock
def test_explicit_refresh_rejected_keeps_tokens(sync_client) -> None:
    sync_client.tokens.set_token("still-valid")
    sync_client.tokens.set_refresh_token("R1")
    respx.post(f"{BASE_URL}/auth/refresh").mock(return_value=INVALID_GRANT)

    with pytest.raises(MDLAuthError) as excinfo:
        sync_client.auth.refresh()

    assert excinfo.value.message == "The provided authorization grant is invalid."
    assert sync_client.tokens.get_token() == "still-valid"


def test_explicit_refresh_without_refresh_token(sync_client) -> None:
    with pytest.raises(MDLConfigError):
        sync_client.auth.refresh()


@respx.mock
async def test_explicit_refresh_401_keeps_tokens_async(async_client) -> None:
    async_client.tokens.set_token("still-valid")
    async_client.tokens.set_refresh_token("R1")
    respx.post(f"{BASE_URL}/auth/refresh").mock(return_value=EXPIRED)

    with pytest.raises(MDLAuthError):
        await async_client.auth.refresh()

    assert async_client.tokens.get_token() == "still-valid"
    assert async_client.tokens.get_refresh_token() == "R1"


@respx.mock
async def test_explicit_refresh_async(async_client) -> None:
    async_client.tokens.set_refresh_token("R1")
    respx.post(f"{BASE_URL}/auth/refresh").mock(return_value=Response(200, json=NEW_PAIR))

    auth = await async_client.auth.refresh()

    assert auth.access_token == "new"
    assert async_client.tokens.get_token() == "new"


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self.text = json.dumps(payload)
        self.headers: dict[str, str] = {}


class _ConcurrentExpiryClient:
    """Holds every request made with the old token until two have arrived, then 401s them."""

    def __init__(self) -> None:
        self.old_token_requests = 0
        self.both_sent = asyncio.Event()
        self.refresh_calls = 0

    async def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        if url.endswith("/auth/refresh"):
            self.refresh_calls += 1
            await asyncio.sleep(0)
            return _FakeResponse(200, NEW_PAIR)
        if kwargs["headers"].get("Authorization") == "Bearer old":
            self.old_token_requests += 1
            if self.old_token_requests == 2:
                self.both_sent.set()
            await self.both_sent.wait()
            return _FakeResponse(401, {"code": 401, "message": "Invalid access token."})
        return _FakeResponse(200, {"username": "alice"})


class _ThreadedExpiryClient:
    """Sync twin of :class:`_ConcurrentExpiryClient`, for two threads."""

    def __init__(self) -> None:
        self.both_sent = threading.Barrier(2, timeout=5)
        self.refresh_calls = 0

    def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        if url.endswith("/auth/refresh"):
            self.refresh_calls += 1
            return _FakeResponse(200, NEW_PAIR)
        if kwargs["headers"].get("Authorization") == "Bearer old":
            self.both_sent.wait()
            return _FakeResponse(401, {"code": 401, "message": "Invalid access token."})
        return _FakeResponse(200, {"username": "alice"})


def test_concurrent_401s_refresh_once_across_threads() -> None:
    http_client = _ThreadedExpiryClient()
    client = MDLClient(api_key=API_KEY, token="old", http_client=http_client)
    client.tokens.set_refresh_token("R1")

    with ThreadPoolExecutor(max_workers=2) as pool:
        profiles = list(pool.map(lambda _: client.account.get_profile(), range(2)))

    assert [p.username for p in profiles] == ["alice", "alice"]
    assert http_client.refresh_calls == 1
    assert client.tokens.get_token() == "new"


async def test_concurrent_401s_refresh_once() -> None:
    http_client = _ConcurrentExpiryClient()
    client = AsyncMDLClient(api_key=API_KEY, token="old", http_client=http_client)
    client.tokens.set_refresh_token("R1")

    first, second = await asyncio.gather(
        client.account.get_profile(), client.account.get_profile()
    )

    assert first.username == second.username == "alice"
    # The second request waits for the lock and reuses the pair the first one fetched;
    # spending the rotated refresh token twice would fail.
    assert http_client.refresh_calls == 1
    assert client.tokens.get_token() == "new"
