"""Titles/search/explore resource tests — request shape and response parsing."""

from __future__ import annotations

import json

import respx
from httpx import Response
from tests.conftest import API_KEY, BASE_URL


@respx.mock
def test_get_title_sync(sync_client) -> None:
    route = respx.get(f"{BASE_URL}/titles/686").mock(
        return_value=Response(200, json={"id": 686, "title": "My Title", "rating": 8.5})
    )
    title = sync_client.titles.get_title(686)

    assert title.id == 686
    assert title.title == "My Title"
    assert title.rating == 8.5
    request = route.calls.last.request
    assert request.headers["mdl-api-key"] == API_KEY
    assert request.headers["version"] == "2.3.3"
    assert request.url.params["expand"] == "1"
    # get_title is an unauthenticated endpoint.
    assert "Authorization" not in request.headers


@respx.mock
async def test_get_title_async(async_client) -> None:
    respx.get(f"{BASE_URL}/titles/686").mock(
        return_value=Response(200, json={"id": 686, "title": "My Title"})
    )
    title = await async_client.titles.get_title(686)
    assert title.id == 686
    assert title.title == "My Title"


@respx.mock
def test_recommendations_parses_list(sync_client) -> None:
    respx.get(f"{BASE_URL}/titles/686/recommendations").mock(
        return_value=Response(200, json=[{"id": 1, "title": "A"}, {"id": 2, "title": "B"}])
    )
    recs = sync_client.titles.get_recommendations(686)
    assert [r.id for r in recs] == [1, 2]


@respx.mock
def test_search_titles_request_shape(sync_client) -> None:
    route = respx.post(url__regex=rf"{BASE_URL}/search/titles.*").mock(
        return_value=Response(200, json=[{"id": 5, "title": "Found"}])
    )
    results = sync_client.search.titles("signal", page=2, synopsis=True)
    assert results[0].title == "Found"
    params = route.calls.last.request.url.params
    assert params["q"] == "signal"
    assert params["page"] == "2"
    assert params["edge"] == "1"
    assert params["synopsis"] == "1"


@respx.mock
def test_explore_trending_uses_path(sync_client) -> None:
    route = respx.get(f"{BASE_URL}/titles/trending").mock(
        return_value=Response(200, json=[{"id": 9, "title": "Hot"}])
    )
    out = sync_client.explore.trending()
    assert out[0].id == 9
    assert route.called


@respx.mock
def test_comment_count_reads_pagination_header(sync_client) -> None:
    respx.get(f"{BASE_URL}/titles/686/comments").mock(
        return_value=Response(200, json=[], headers={"x-pagination-total": "42"})
    )
    assert sync_client.titles.get_comment_count(686) == 42


@respx.mock
def test_submit_review_body(sync_client) -> None:
    sync_client.tokens.set_token("tok")
    route = respx.post(f"{BASE_URL}/reviews").mock(
        return_value=Response(200, json="success")
    )
    result = sync_client.reviews.submit(
        review="Great show", headline="Loved it", overall=9.0, completed=True
    )
    assert result == "success"
    body = json.loads(route.calls.last.request.content)
    assert body["headline"] == "Loved it"
    assert body["ratings"]["overall"] == 9.0
    assert body["completed"] is True
    assert route.calls.last.request.headers["Authorization"] == "Bearer tok"
