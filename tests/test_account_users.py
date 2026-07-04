"""Account settings, people/users, and comments resource tests."""

from __future__ import annotations

import json

import respx
from httpx import Response
from tests.conftest import BASE_URL

from mdl.auth import md5_password


@respx.mock
def test_get_profile_parses_images(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/users/settings").mock(
        return_value=Response(
            200,
            json={
                "username": "alice",
                "email": "a@example.com",
                "images": {"thumb": "u/1_t.jpg", "poster": "u/1_p.jpg"},
                "vip": True,
            },
        )
    )
    profile = sync_client.account.get_profile()
    assert profile.username == "alice"
    assert profile.vip is True
    assert profile.images.thumb == "u/1_t.jpg"


@respx.mock
def test_update_profile_info_setting_param_and_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.patch(url__regex=rf"{BASE_URL}/users/settings.*").mock(
        return_value=Response(200, json="")
    )
    result = sync_client.account.update_profile_info(display_name="Al", location="KR")
    assert result == ""
    request = route.calls.last.request
    assert request.url.params["setting"] == "account"
    body = json.loads(request.content)
    assert body["display_name"] == "Al"
    assert body["location"] == "KR"


@respx.mock
def test_update_email_hashes_password(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.patch(url__regex=rf"{BASE_URL}/users/settings.*").mock(
        return_value=Response(200, json={"username": "alice", "email": "new@example.com"})
    )
    profile = sync_client.account.update_email("new@example.com", "secret")
    assert profile.email == "new@example.com"
    body = json.loads(route.calls.last.request.content)
    assert body["password"] == md5_password("secret")


@respx.mock
def test_get_privacy_reads_nested_value(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/users/settings/privacy").mock(
        return_value=Response(200, json={"profile": {"read": {"feeds": 3}}})
    )
    assert sync_client.account.get_privacy() == 3


@respx.mock
def test_get_privacy_defaults_to_minus_two(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/users/settings/privacy").mock(
        return_value=Response(200, json={})
    )
    assert sync_client.account.get_privacy() == -2


@respx.mock
def test_upload_profile_image_is_multipart(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post("https://app-api.mydramalist.com/upload/bearer").mock(
        return_value=Response(200, json={"filename": "x.jpg", "url": "http://i/x.jpg"})
    )
    result = sync_client.account.upload_profile_image(b"\xff\xd8\xff", filename="me.jpg")
    assert result.filename == "x.jpg"
    request = route.calls.last.request
    # multipart strips the JSON content-type and keeps the api key
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert request.headers["mdl-api-key"] == "test-api-key"


@respx.mock
def test_verify_purchase_query_and_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(url__regex=rf"{BASE_URL}/iap/verify.*").mock(
        return_value=Response(200, json={"success": True})
    )
    ok = sync_client.account.verify_purchase({"receipt": "abc"}, type="coins")
    assert ok is True
    params = route.calls.last.request.url.params
    assert params["store"] == "playstore"
    assert params["type"] == "coins"


@respx.mock
def test_get_person_and_credits(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/people/42").mock(
        return_value=Response(200, json={"id": 42, "name": "Actor", "thumbnail": "p/42.jpg"})
    )
    respx.get(f"{BASE_URL}/people/42/credits").mock(
        return_value=Response(200, json={"cast": [{"id": 1, "name": "Role"}], "crew": []})
    )
    person = sync_client.users.get_person(42)
    assert person.id == 42
    # thumbnail resolved to absolute image host
    assert person.thumbnail == "https://i.mydramalist.com/p/42.jpg"

    credits = sync_client.users.get_person_credits(42)
    assert credits.cast[0].name == "Role"


@respx.mock
def test_like_person_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/people/42/likes").mock(
        return_value=Response(200, json="ok")
    )
    assert sync_client.users.like_person(42, True) == "ok"
    assert json.loads(route.calls.last.request.content) == {"liked": True}


@respx.mock
def test_comments_post_body_and_parse(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/comments").mock(
        return_value=Response(200, json={"total": 1, "comments": [{"id": 7, "message": "hi"}]})
    )
    reply = sync_client.comments.post(pid=686, ptype="title", message="hi", spoiler=0)
    assert reply.total == 1
    assert reply.comments[0].id == 7
    body = json.loads(route.calls.last.request.content)
    assert body == {"pid": 686, "ptype": "title", "message": "hi", "spoiler": 0}


@respx.mock
def test_comments_like_and_delete(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.post(f"{BASE_URL}/comments/9/likes").mock(return_value=Response(200, json=True))
    respx.delete(f"{BASE_URL}/comments/9").mock(return_value=Response(200, json=True))
    assert sync_client.comments.like(9) is True
    assert sync_client.comments.delete(9) is True
