"""Watchlist writes (save/update/remove), sync failures, calendar timestamps and user stats.

Payload shapes are trimmed from live API responses.
"""

from __future__ import annotations

import datetime as dt
import json

import httpx
import pytest
import respx
from httpx import Response
from tests.conftest import BASE_URL

from mdl import MDLConnectionError, MDLError, MDLSyncError
from mdl.models import Movie, MovieStatusType, MovieTitle

TITLE_ID = 713793


def _progress(**overrides: object) -> dict:
    entry = {
        "list_id": 1,
        "episode_seen": 4,
        "rating": 8,
        "priority": 0,
        "times_rewatched": 0,
        "rewatch_value": 0,
        "date_start": "2026-11-13",
        "date_finish": "0000-00-00",
        "note": "",
        "tags": "",
        "deleted": False,
        "watch_points": {"production": False, "story": False},
        "updated_at": "2026-11-13T12:19:37Z",
        "created_at": "0001-01-01T00:00:00Z",
        "title": {"id": TITLE_ID, "title": "Fake It Till You Make It", "episodes": 14},
    }
    entry.update(overrides)
    return entry


def _sent(route: respx.Route, call: int = -1) -> list:
    return json.loads(route.calls[call].request.content)


@respx.mock
def test_save_sends_array_identified_by_title_id(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )
    movie = Movie.model_validate(_progress(id=356552072))

    result = sync_client.watchlist.save([movie])

    assert result.success.titles == 1
    assert result.failures == []
    (body,) = _sent(route)
    assert body["title"] == {"id": TITLE_ID}
    assert body["list_id"] == 1 and body["rating"] == 8 and body["episode_seen"] == 4
    # Response-only fields are not sent back.
    assert not {"id", "updated_at", "created_at", "deleted"} & set(body)


@respx.mock
def test_add_wraps_a_single_entry_in_an_array(sync_client) -> None:
    sync_client.tokens.set_token("t")
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )
    sync_client.watchlist.add({"list_id": 3, "title": {"id": TITLE_ID}})
    assert _sent(route) == [{"list_id": 3, "title": {"id": TITLE_ID}}]


@respx.mock
def test_update_keeps_fields_that_are_not_passed(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        return_value=Response(200, json=_progress(note="loved it"))
    )
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )

    saved = sync_client.watchlist.update(TITLE_ID, episode_seen=5)

    assert saved.episode_seen == 5
    (body,) = _sent(route)
    assert body["episode_seen"] == 5
    # A partial body would reset these, so the current values are sent back.
    assert body["rating"] == 8
    assert body["list_id"] == 1
    assert body["note"] == "loved it"
    assert body["date_start"] == "2026-11-13"
    assert route.call_count == 1


@respx.mock
def test_update_completed_marks_every_episode_seen(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        return_value=Response(200, json=_progress())
    )
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )

    sync_client.watchlist.update(
        TITLE_ID, status=MovieStatusType.COMPLETED, date_finish=dt.date(2026, 11, 13)
    )

    (body,) = _sent(route)
    assert body["list_id"] == 2
    assert body["episode_seen"] == 14
    assert body["date_finish"] == "2026-11-13"


@respx.mock
def test_update_adds_title_and_resaves_when_server_restores_old_entry(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        side_effect=[
            # Not on a list yet.
            Response(200, json=_progress(list_id=0, episode_seen=0, rating=0)),
            # The first save of a once-removed title brings back its old progress.
            Response(200, json=_progress(list_id=3, episode_seen=14, rating=0)),
        ]
    )
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )

    sync_client.watchlist.update(TITLE_ID, status="plantowatch", episode_seen=0)

    assert route.call_count == 2
    assert _sent(route, 1)[0]["episode_seen"] == 0
    assert _sent(route, 1)[0]["list_id"] == 3


@respx.mock
def test_update_adds_title_without_resave_when_stored_matches(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        side_effect=[
            Response(200, json=_progress(list_id=0, episode_seen=0, rating=0)),
            Response(200, json=_progress(list_id=1, episode_seen=2, rating=0)),
        ]
    )
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )

    sync_client.watchlist.update(TITLE_ID, status=MovieStatusType.WATCHING, episode_seen=2)

    assert route.call_count == 1


@respx.mock
def test_update_requires_status_for_title_on_no_list(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        return_value=Response(200, json=_progress(list_id=0))
    )
    route = respx.post(f"{BASE_URL}/sync/mylist")

    with pytest.raises(ValueError, match="status is required"):
        sync_client.watchlist.update(TITLE_ID, episode_seen=1)
    assert not route.called


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"rating": 11}, "rating"),
        ({"episode_seen": -1}, "negative"),
        ({"status": MovieStatusType.UNDECIDED}, "not supported"),
        ({"status": "bogus"}, "bogus"),
    ],
)
def test_update_rejects_bad_arguments_before_any_request(sync_client, kwargs, match) -> None:
    with pytest.raises(ValueError, match=match):
        sync_client.watchlist.update(TITLE_ID, current=Movie.model_validate(_progress()), **kwargs)


@respx.mock
def test_update_raises_sync_error_with_server_reason(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(
            200,
            json={
                "success": {"titles": 0},
                "failed": {
                    "titles": [
                        {"id": TITLE_ID, "message": "code=400, message=Invalid episode seen value."}
                    ]
                },
            },
        )
    )

    with pytest.raises(MDLSyncError) as excinfo:
        sync_client.watchlist.update(
            TITLE_ID, episode_seen=999, current=Movie.model_validate(_progress())
        )

    assert str(excinfo.value) == "Invalid episode seen value."
    assert excinfo.value.failures[0].id == TITLE_ID


@respx.mock
def test_get_progress_for_title_on_no_list(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(return_value=Response(200, json={}))
    progress = sync_client.watchlist.get_progress(TITLE_ID)
    assert progress.list_id == 0
    assert progress.status is None
    assert progress.title.id == TITLE_ID


@respx.mock
def test_remove_reports_deleted_count(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.delete(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"deleted": {"titles": 1}})
    )
    assert sync_client.watchlist.remove([TITLE_ID]).deleted == {"titles": 1}


@respx.mock
async def test_update_async(async_client) -> None:
    async_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        return_value=Response(200, json=_progress())
    )
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )
    saved = await async_client.watchlist.update(TITLE_ID, rating=9.5)
    assert saved.rating == 9.5
    assert _sent(route)[0]["episode_seen"] == 4


def test_status_list_ids_round_trip() -> None:
    assert MovieStatusType.WATCHING.list_id == 1
    assert MovieStatusType.NOT_INTERESTED.list_id == 6
    assert MovieStatusType.UNDECIDED.list_id is None
    for status in MovieStatusType:
        if status.list_id is not None:
            assert MovieStatusType.from_list_id(status.list_id) is status
    assert MovieStatusType.from_list_id(0) is None
    assert Movie(list_id=2, title=MovieTitle(id=1)).status is MovieStatusType.COMPLETED


@respx.mock
def test_calendar_episodes_parse_unix_timestamps(sync_client) -> None:
    respx.post(f"{BASE_URL}/calendar/episodes").mock(
        return_value=Response(
            200,
            json={
                "items": [
                    {
                        "id": 6831194,
                        "rid": 811486,
                        "episode_number": 4,
                        "released_at": 1794653400,
                        "duration": 54,
                        "original_release_date": 1794048600,
                        "permalink": "/811486-world-dice-tour-season-4/episode/4",
                    }
                ],
                "relationships": [
                    {
                        "id": 811486,
                        "title": "World Dice Tour 4",
                        "type": "TV Show",
                        "url": "/811486-world-dice-tour-season-4",
                        "genres": "Variety",
                        "timezone": "Asia/Seoul",
                        "add_status": True,
                    }
                ],
            },
        )
    )

    calendar = sync_client.calendar.episodes()

    item = calendar.items[0]
    assert item.released_at == 1794653400
    assert item.released_datetime == dt.datetime(2026, 11, 14, 10, 50, tzinfo=dt.timezone.utc)
    assert item.original_release_datetime is not None
    assert calendar.title_for(item).title == "World Dice Tour 4"
    assert calendar.relationships[0].add_status is True


@respx.mock
def test_user_stats(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/users/someone/stats").mock(
        return_value=Response(
            200,
            json={
                "mylists": {
                    "completed": [{"type": "Drama", "collected": 209, "minutes": 163680}],
                    "plantowatch": [{"type": "Movie", "collected": 76}],
                },
                "stats": [
                    {"type": "Movie", "collected": 62, "minutes": 6266, "watched": 62},
                    {"type": "Shows", "collected": 522, "minutes": 245708, "watched": 4914},
                ],
                "ratings": {"total": 3, "distribution": {"10.0": 1, "8.0": 2, "5.5": 0}},
                "comments": 106,
                "friends": 22,
            },
        )
    )

    stats = sync_client.users.get_user_stats("someone")

    assert stats.total().minutes == 251974
    assert stats.total("Shows").watched == 4914
    assert stats.total("Movie").watched == 62
    assert stats.mylists["completed"][0].collected == 209
    assert stats.ratings.mean == pytest.approx(26 / 3)
    assert stats.friends == 22


@respx.mock
def test_transport_failure_raises_connection_error(sync_client) -> None:
    respx.get(f"{BASE_URL}/genres").mock(side_effect=httpx.ConnectTimeout("timed out"))

    with pytest.raises(MDLConnectionError, match="ConnectTimeout") as excinfo:
        sync_client.titles.get_genres()

    assert isinstance(excinfo.value, MDLError)
    assert isinstance(excinfo.value.__cause__, httpx.ConnectTimeout)


@respx.mock
def test_refresh_outage_raises_connection_error_and_keeps_tokens(sync_client) -> None:
    sync_client.tokens.set_token("expired")
    sync_client.tokens.set_refresh_token("refresh")
    respx.get(f"{BASE_URL}/users/settings").mock(return_value=Response(401, json={}))
    respx.post(f"{BASE_URL}/auth/refresh").mock(side_effect=httpx.ReadTimeout("timed out"))

    with pytest.raises(MDLConnectionError):
        sync_client.account.get_profile()

    # A refresh that never reached the server is not a rejection.
    assert sync_client.tokens.get_refresh_token() == "refresh"


@respx.mock
def test_update_unknown_title_raises_sync_error(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(
            200, json={"success": {"titles": 0}, "not_found": {"titles": [{"id": 999999999}]}}
        )
    )
    current = Movie(list_id=3, title=MovieTitle(id=999999999))

    with pytest.raises(MDLSyncError, match="Title not found") as excinfo:
        sync_client.watchlist.update(999999999, episode_seen=0, current=current)

    assert excinfo.value.failures[0].id == 999999999


@respx.mock
def test_update_resaves_when_restored_entry_has_old_rewatch_count(sync_client) -> None:
    sync_client.tokens.set_token("t")
    respx.get(f"{BASE_URL}/titles/{TITLE_ID}/progress").mock(
        side_effect=[
            Response(200, json=_progress(list_id=0, episode_seen=0, rating=0)),
            # Only the restored rewatch count differs; the server-set start date does not
            # count as a difference.
            Response(
                200,
                json=_progress(list_id=1, episode_seen=0, rating=0, times_rewatched=2),
            ),
        ]
    )
    route = respx.post(f"{BASE_URL}/sync/mylist").mock(
        return_value=Response(200, json={"success": {"titles": 1}})
    )

    sync_client.watchlist.update(TITLE_ID, status="watching", episode_seen=0)

    assert route.call_count == 2
