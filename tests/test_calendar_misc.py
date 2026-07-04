"""Subscription, flowers, awards, reports, calendar and leaderboard resource tests."""

from __future__ import annotations

import json

import respx
from httpx import Response
from tests.conftest import BASE_URL


@respx.mock
def test_subscription_get(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/subscriptions").mock(
        return_value=Response(
            200,
            json={"settings": {"vip_status": True, "hide_ads": True}, "history": []},
        )
    )
    sub = sync_client.subscription.get()
    assert sub.settings.vip_status is True
    assert sub.settings.hide_ads is True


@respx.mock
def test_flowers_send_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/people/7/gift_process").mock(
        return_value=Response(200, json=True)
    )
    assert sync_client.flowers.send(7, 10) is True
    assert json.loads(route.calls.last.request.content) == {"amount": 10}


@respx.mock
def test_flowers_gift_process_parse(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/people/7/gift_process").mock(
        return_value=Response(200, json={"balance": 100, "price": 5, "prices": [5, 10]})
    )
    process = sync_client.flowers.gift_process(7)
    assert process.balance == 100
    assert process.prices == [5, 10]


@respx.mock
def test_awards_give_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/awards/3").mock(return_value=Response(200, json=True))
    ok = sync_client.awards.give(
        3, ref_id=686, ref_type="title", ptype="title", pid=686, anonymous=True
    )
    assert ok is True
    body = json.loads(route.calls.last.request.content)
    assert body["award_id"] == 3
    assert body["anonymous"] is True
    assert body["ptype"] == "title"


@respx.mock
def test_reports_submit_body(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/reports").mock(return_value=Response(200, json="ok"))
    result = sync_client.reports.submit(
        pid=5, ptype="comment", comment="bad", type="spam", reason="off-topic"
    )
    assert result == "ok"
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "pid": 5,
        "ptype": "comment",
        "comment": "bad",
        "type": "spam",
        "reason": "off-topic",
    }


@respx.mock
def test_calendar_episodes_and_quarter(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.post(f"{BASE_URL}/calendar/episodes").mock(
        return_value=Response(200, json={"items": [{"id": 1, "episode_number": 3}]})
    )
    route = respx.post(f"{BASE_URL}/calendar/quarter").mock(
        return_value=Response(200, json=[{"id": 1, "title": "Q Show", "rating": 8.1}])
    )
    episodes = sync_client.calendar.episodes()
    assert episodes.items[0].episode_number == 3

    quarter = sync_client.calendar.quarter(year=2024, quarter="Q1")
    assert quarter[0].title == "Q Show"
    assert json.loads(route.calls.last.request.content) == {"year": 2024, "quarter": "Q1"}


@respx.mock
def test_leaderboard_period_mapping_and_entries_key(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.get(url__regex=rf"{BASE_URL}/people/leaderboard.*").mock(
        return_value=Response(
            200,
            json={"time_period": "weekly", "entries": [{"id": 1, "display_name": "Top"}]},
        )
    )
    # int 1 maps to the "weekly" period; entries are unwrapped from the wrapper object
    entries = sync_client.leaderboard.get(1)
    assert entries[0].display_name == "Top"
    assert route.calls.last.request.url.params["time_period"] == "weekly"


@respx.mock
async def test_leaderboard_async_string_period(async_client) -> None:
    route = respx.get(url__regex=rf"{BASE_URL}/people/leaderboard.*").mock(
        return_value=Response(200, json={"entries": []})
    )
    await async_client.leaderboard.get("alltime")
    assert route.calls.last.request.url.params["time_period"] == "alltime"
