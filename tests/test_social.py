"""Feeds, articles, friends, messages, notifications and groups resource tests."""

from __future__ import annotations

import json

import respx
from httpx import Response
from tests.conftest import BASE_URL


@respx.mock
def test_feeds_create_body_optional_fields(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/feeds").mock(
        return_value=Response(200, json={"items": [{"id": 1, "message": "hello"}]})
    )
    resp = sync_client.feeds.create(message="hello", tag_id=5, tag_type="title")
    assert resp.items[0].message == "hello"
    body = json.loads(route.calls.last.request.content)
    assert body["message"] == "hello"
    assert body["privacy"] == "public"
    assert body["spoiler"] is False
    assert body["tag_id"] == 5
    assert body["tag_type"] == "title"
    # optional fields left unset are not sent
    assert "embed_id" not in body
    assert "group_id" not in body


@respx.mock
def test_feeds_get_numeric_adds_where_param(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(url__regex=rf"{BASE_URL}/feeds/123.*").mock(
        return_value=Response(200, json={"id": 123, "message": "m"})
    )
    feed = sync_client.feeds.get(123)
    assert feed.id == 123
    assert route.calls.last.request.url.params["where"] == "id"


@respx.mock
def test_feeds_like_and_delete_and_hide(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/feeds/9/likes").mock(return_value=Response(200, json=True))
    respx.delete(f"{BASE_URL}/feeds/9").mock(return_value=Response(200, json=True))
    respx.post(f"{BASE_URL}/feeds/9/hide").mock(return_value=Response(200, json=True))
    assert sync_client.feeds.like(9, True) is True
    assert sync_client.feeds.delete(9) is True
    assert sync_client.feeds.hide(9) is True
    assert json.loads(route.calls.last.request.content) == {"liked": True}


@respx.mock
def test_feeds_upload_image_multipart_category(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post("https://app-api.mydramalist.com/upload/bearer").mock(
        return_value=Response(200, json={"filename": "p.jpg"})
    )
    result = sync_client.feeds.upload_image(b"\xff\xd8", filename="p.jpg")
    assert result.filename == "p.jpg"
    content_type = route.calls.last.request.headers["content-type"]
    assert content_type.startswith("multipart/form-data")


@respx.mock
def test_fetch_embed_url_param(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(url__regex=rf"{BASE_URL}/embed.*").mock(
        return_value=Response(200, json={"title": "Embedded", "type": "video"})
    )
    embed = sync_client.feeds.fetch_embed("https://youtu.be/x")
    assert embed.title == "Embedded"
    assert route.calls.last.request.url.params["url"] == "https://youtu.be/x"


@respx.mock
def test_articles_featured_and_get(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(url__regex=rf"{BASE_URL}/articles/featured.*").mock(
        return_value=Response(200, json=[{"id": 1, "title": "A"}])
    )
    respx.get(f"{BASE_URL}/articles/1").mock(
        return_value=Response(200, json={"id": 1, "title": "A", "total_likes": 3})
    )
    featured = sync_client.articles.featured(page=2)
    assert featured[0].title == "A"
    article = sync_client.articles.get(1)
    assert article.total_likes == 3


@respx.mock
def test_friends_requests_and_unfriend(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(url__regex=rf"{BASE_URL}/users/requests.*").mock(
        return_value=Response(200, json=[{"username": "bob", "display_name": "Bob"}])
    )
    respx.delete(f"{BASE_URL}/users/8/unfriend").mock(return_value=Response(200, json=True))
    reqs = sync_client.friends.requests(page=1)
    assert reqs[0].username == "bob"
    assert route.calls.last.request.url.params["page"] == "1"
    assert sync_client.friends.unfriend(8) is True


@respx.mock
def test_messages_reply_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/users/inbox/3").mock(return_value=Response(200, json=True))
    assert sync_client.messages.reply(3, "hey") is True
    assert json.loads(route.calls.last.request.content) == {"from": "inbox", "message": "hey"}


@respx.mock
def test_messages_thread_parse(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/users/inbox/3").mock(
        return_value=Response(
            200,
            json={"messages": [{"id": 1, "message": "hi"}], "stats": {"total": 1}},
        )
    )
    thread = sync_client.messages.thread(3)
    assert thread.messages[0].message == "hi"
    assert thread.stats.total == 1


@respx.mock
def test_notifications_fetch_and_from_alias(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(url__regex=rf"{BASE_URL}/notifications.*").mock(
        return_value=Response(
            200,
            json={
                "notifications": [{"id": 1, "message": "n", "from": {"username": "u"}}],
                "total": 1,
            },
        )
    )
    notifs = sync_client.notifications.fetch(page=1)
    assert notifs.total == 1
    assert notifs.notifications[0].from_.username == "u"


@respx.mock
def test_groups_join_leave(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.post(f"{BASE_URL}/groups/4/join").mock(
        return_value=Response(200, json={"id": 4, "name": "G", "is_member": True})
    )
    respx.post(f"{BASE_URL}/groups/4/leave").mock(
        return_value=Response(200, json={"id": 4, "name": "G", "is_member": False})
    )
    joined = sync_client.groups.join(4)
    assert joined.is_member is True
    left = sync_client.groups.leave(4)
    assert left.is_member is False
