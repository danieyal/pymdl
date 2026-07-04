"""Custom-list resource tests: discovery feeds, CRUD, items, votes."""

from __future__ import annotations

import json

import respx
from httpx import Response
from tests.conftest import BASE_URL


@respx.mock
def test_trending_feed_params(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(f"{BASE_URL}/lists/trending").mock(
        return_value=Response(200, json=[{"name": "Best of 2024", "slug": "best"}])
    )
    lists = sync_client.custom_lists.trending(page=3, limit=10)
    assert lists[0].name == "Best of 2024"
    params = route.calls.last.request.url.params
    assert params["page"] == "3"
    assert params["limit"] == "10"


@respx.mock
def test_get_user_lists_path(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(f"{BASE_URL}/users/55/lists").mock(
        return_value=Response(200, json=[{"name": "Mine"}])
    )
    lists = sync_client.custom_lists.get_user_lists(55)
    assert lists[0].name == "Mine"
    assert route.called


@respx.mock
def test_create_list_body_defaults(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/lists").mock(
        return_value=Response(200, json={"name": "New", "slug": "new"})
    )
    created = sync_client.custom_lists.create(name="New", description="d")
    assert created.name == "New"
    body = json.loads(route.calls.last.request.content)
    assert body["name"] == "New"
    assert body["sort_by"] == "default"
    assert body["vote_limit"] == 100
    assert body["max_num_items"] == 100
    assert body["add_permission"] is True


@respx.mock
def test_add_item_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/lists/12/add").mock(return_value=Response(200, json=True))
    assert sync_client.custom_lists.add_item(12, 686) is True
    assert json.loads(route.calls.last.request.content) == {"entry_id": 686}


@respx.mock
def test_remove_and_sort_item(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.delete(f"{BASE_URL}/lists/12/99").mock(return_value=Response(200, json=True))
    route = respx.patch(f"{BASE_URL}/lists/12/99/order").mock(
        return_value=Response(200, json=True)
    )
    assert sync_client.custom_lists.remove_item(12, 99) is True
    assert sync_client.custom_lists.sort_item(12, 99, 2.5) is True
    assert json.loads(route.calls.last.request.content) == {"order": 2.5}


@respx.mock
def test_get_detail_and_watch_status(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/lists/12").mock(
        return_value=Response(
            200, json={"id": 12, "name": "L", "items": [{"id": 1, "title": "T"}]}
        )
    )
    respx.get(f"{BASE_URL}/lists/12/watched").mock(
        return_value=Response(200, json=[{"id": 1, "name": "Completed", "total": 5}])
    )
    detail = sync_client.custom_lists.get_detail(12)
    assert detail.id == 12
    assert detail.items[0].title == "T"

    watched = sync_client.custom_lists.get_watch_status(12)
    assert watched[0].name == "Completed"
    assert watched[0].total == 5


@respx.mock
def test_like_returns_like_model(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.post(f"{BASE_URL}/lists/12/likes").mock(
        return_value=Response(200, json={"id": 12, "likes": 4, "liked": True})
    )
    like = sync_client.custom_lists.like(12, True)
    assert like.likes == 4
    assert like.liked is True
