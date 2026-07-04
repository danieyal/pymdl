"""Auth resource tests: MD5 hashing, device id, token storage."""

from __future__ import annotations

import json

import respx
from httpx import Response
from tests.conftest import BASE_URL

from mdl.auth import md5_password


@respx.mock
def test_login_hashes_password_and_stores_token(sync_client) -> None:
    route = respx.post(url__regex=rf"{BASE_URL}/auth/login.*").mock(
        return_value=Response(200, json={"access_token": "TOKEN", "refresh_token": "R"})
    )
    auth = sync_client.auth.login("alice", "hunter2", device_id="dev-123")

    assert auth.access_token == "TOKEN"
    # token is now stored and reused on subsequent requests
    assert sync_client.tokens.get_token() == "TOKEN"
    assert sync_client.tokens.get_refresh_token() == "R"

    request = route.calls.last.request
    body = json.loads(request.content)
    assert body["username"] == "alice"
    assert body["password"] == md5_password("hunter2")
    assert request.url.params["device_id"] == "dev-123"
    # login is unauthenticated
    assert "Authorization" not in request.headers


@respx.mock
async def test_login_async(async_client) -> None:
    respx.post(url__regex=rf"{BASE_URL}/auth/login.*").mock(
        return_value=Response(200, json={"access_token": "T2"})
    )
    auth = await async_client.auth.login("bob", "pw", device_id="d")
    assert auth.access_token == "T2"
    assert async_client.tokens.get_token() == "T2"


@respx.mock
def test_register_unwraps_success_block(sync_client) -> None:
    respx.post(f"{BASE_URL}/users").mock(
        return_value=Response(
            200,
            json={"success": True, "message": "ok", "data": {"access_token": "NEW"}},
        )
    )
    auth = sync_client.auth.register("carol", "c@example.com", "pw")
    assert auth.access_token == "NEW"


def test_logout_clears_tokens(sync_client) -> None:
    sync_client.tokens.set_token("x")
    sync_client.auth.logout()
    assert sync_client.tokens.get_token() is None
