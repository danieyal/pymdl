"""Watchlist sync bodies, status-path segments, and error handling."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response
from tests.conftest import BASE_URL

from mdl.errors import MDLAuthError, MDLNotFoundError
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
