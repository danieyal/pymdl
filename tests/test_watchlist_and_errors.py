"""Watchlist sync bodies, status-path segments, and error handling."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response
from tests.conftest import BASE_URL

from mdl.errors import (
    MDLAuthError,
    MDLLoginRequiredError,
    MDLNetworkError,
    MDLNotFoundError,
)
from mdl.models import MovieStatusType


@respx.mock
def test_fetch_watchlist_status_segment(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(f"{BASE_URL}/sync/mylist/completed").mock(
        return_value=Response(200, json=[{"list_id": 1, "title": {"id": 9, "title": "Z"}}])
    )
    movies = sync_client.watchlist.fetch(MovieStatusType.COMPLETED)
    assert movies[0].list_id == 1
    assert movies[0].title.id == 9
    assert route.called


@pytest.mark.parametrize("status", [MovieStatusType.WATCHING, "watching"])
@respx.mock
def test_fetch_watching_uses_watchlist_segment(sync_client, status) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(f"{BASE_URL}/sync/mylist/watchlist").mock(
        return_value=Response(200, json=[{"list_id": 1, "title": {"id": 9}}])
    )
    movies = sync_client.watchlist.fetch(status)
    assert movies[0].title.id == 9
    assert route.called


def test_mylist_path_maps_watching_to_watchlist() -> None:
    assert MovieStatusType.WATCHING.mylist_path() == "/sync/mylist/watchlist"
    assert MovieStatusType.PLAN_TO_WATCH.mylist_path() == "/sync/mylist/plantowatch"


@respx.mock
def test_remove_sends_json_array_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.delete(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 2}})
    )
    result = sync_client.watchlist.remove([11, 22])
    assert result.success.titles == 2
    body = json.loads(route.calls.last.request.content)
    assert body == [{"id": 11}, {"id": 22}]


@respx.mock
def test_last_activities_404_returns_default(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/sync/last_activities").mock(return_value=Response(404, json={}))
    activity = sync_client.watchlist.get_last_activities()
    assert activity.all is None  # default empty object, not an exception


@respx.mock
def test_401_clears_token_and_raises_auth_error(sync_client) -> None:
    sync_client.tokens.set_token("stale")
    respx.get(f"{BASE_URL}/users/settings").mock(
        return_value=Response(401, json={"error": "unauthorized"})
    )
    with pytest.raises(MDLAuthError) as excinfo:
        sync_client.account.get_profile()
    assert excinfo.value.status_code == 401
    assert excinfo.value.message == "unauthorized"
    # token cleared on 401
    assert sync_client.tokens.get_token() is None


@respx.mock
def test_anonymous_bare_400_raises_login_required(sync_client) -> None:
    # Login-only endpoints answer an anonymous request with a bare text/plain 400.
    respx.get(f"{BASE_URL}/titles/1").mock(
        return_value=Response(
            400,
            text='{"code":400,"message":"Bad Request"}\n',
            headers={"Content-Type": "text/plain; charset=utf-8"},
        )
    )
    with pytest.raises(MDLLoginRequiredError) as excinfo:
        sync_client.titles.get_title(1)
    assert isinstance(excinfo.value, MDLAuthError)
    assert excinfo.value.status_code == 400
    assert "auth.login()" in excinfo.value.message


@respx.mock
def test_authenticated_400_is_not_login_required(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/1").mock(
        return_value=Response(400, json={"code": 400, "message": "Bad Request"})
    )
    with pytest.raises(MDLNetworkError) as excinfo:
        sync_client.titles.get_title(1)
    assert not isinstance(excinfo.value, MDLAuthError)
    # the token is kept: only a 401 clears it
    assert sync_client.tokens.get_token() == "t"


@respx.mock
def test_anonymous_validation_400_is_not_login_required(sync_client) -> None:
    respx.get(f"{BASE_URL}/genres").mock(
        return_value=Response(400, json={"code": 400, "message": "Invalid or missing parameters."})
    )
    with pytest.raises(MDLNetworkError) as excinfo:
        sync_client.titles.get_genres()
    assert not isinstance(excinfo.value, MDLAuthError)


@respx.mock
def test_404_raises_not_found(sync_client) -> None:
    respx.get(f"{BASE_URL}/titles/1").mock(
        return_value=Response(404, json={"message": "no such title"})
    )
    with pytest.raises(MDLNotFoundError):
        sync_client.titles.get_title(1)


@respx.mock
async def test_error_async(async_client) -> None:
    respx.get(f"{BASE_URL}/titles/1").mock(return_value=Response(404, json={}))
    with pytest.raises(MDLNotFoundError):
        await async_client.titles.get_title(1)
