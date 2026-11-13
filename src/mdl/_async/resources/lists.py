"""Watchlist sync and custom-list resources (spec §3)."""

from __future__ import annotations

import datetime as _dt
from typing import Any, Iterable, Mapping, Optional, Union

from ..._request import PreparedRequest
from ...errors import MDLNotFoundError, MDLSyncError
from ...models.lists import (
    CustomListDetail,
    CustomListDetailItem,
    CustomListItem,
    CustomListLike,
    WatchStatusList,
)
from ...models.reviews import Comment, CommentReplyResponse, CommentResponse
from ...models.titles import (
    LastActivity,
    Movie,
    MovieStatusType,
    MovieTitle,
    SyncWatchListResponse,
)
from .base import AsyncResource

StatusLike = Union[MovieStatusType, str]
WatchlistEntry = Union[Movie, Mapping[str, Any]]
DateLike = Union[_dt.date, str]

#: Response-only fields that the sync endpoint does not take back.
_READ_ONLY_FIELDS = {"id", "updated_at", "created_at", "deleted"}


def _status_segment(status: StatusLike) -> str:
    try:
        return MovieStatusType(status).mylist_segment
    except ValueError:
        return str(status)


def _date_str(value: Optional[DateLike]) -> Optional[str]:
    if isinstance(value, _dt.date):
        return value.isoformat()
    return value


def _progress_differs(stored: Movie, sent: Movie) -> bool:
    if (stored.list_id, stored.episode_seen) != (sent.list_id, sent.episode_seen):
        return True
    # Dates are left out: the server fills date_start / date_finish on status changes.
    for field in ("rating", "priority", "times_rewatched", "rewatch_value"):
        if (getattr(stored, field) or 0) != (getattr(sent, field) or 0):
            return True
    # An empty note means "keep the stored note", so only a non-empty one must match.
    return bool(sent.note) and stored.note != sent.note


def _entry_body(entry: WatchlistEntry) -> dict[str, Any]:
    if not isinstance(entry, Movie):
        return dict(entry)
    if entry.title is None:
        raise ValueError("A watchlist entry needs a title")
    body = entry.model_dump(exclude_none=True, exclude=_READ_ONLY_FIELDS)
    # The title is identified by id alone; its other fields are server-owned.
    body["title"] = {"id": entry.title.id}
    return body


class WatchlistResource(AsyncResource):
    """WatchListImplRepository — user's list sync."""

    async def fetch(
        self, status: StatusLike, *, last_updated_at: Optional[str] = None
    ) -> list[Movie]:
        """Fetch a status list, e.g. ``/sync/mylist/completed``."""
        params = {"last_updated_at": last_updated_at} if last_updated_at else None
        req = PreparedRequest(
            "GET", f"/sync/mylist/{_status_segment(status)}", params=params
        )
        return self._list(await self._transport.request(req), Movie)

    async def fetch_page(self, status: StatusLike, *, page: int = 1) -> list[Movie]:
        req = PreparedRequest(
            "GET", f"/sync/mylist/{_status_segment(status)}", params={"page": page}
        )
        return self._list(await self._transport.request(req), Movie)

    async def get_last_activities(self) -> LastActivity:
        """``GET /sync/last_activities`` — a 404 yields a default (empty) LastActivity."""
        req = PreparedRequest("GET", "/sync/last_activities")
        try:
            resp = await self._transport.request(req)
        except MDLNotFoundError:
            return LastActivity()
        return self._model(resp, LastActivity)

    async def save(self, entries: Iterable[WatchlistEntry]) -> SyncWatchListResponse:
        """``POST /sync/mylist`` — add or overwrite list entries.

        The body is a JSON array of entries, each naming its title as
        ``{"title": {"id": …}}``. An entry **replaces** the stored one: a field left out
        is reset (an omitted ``rating`` clears the score), so send complete entries or
        use :meth:`update`. Rejected titles are reported in the response's ``failed``
        (see :attr:`SyncWatchListResponse.failures`), not as an HTTP error.
        """
        body = [_entry_body(entry) for entry in entries]
        req = PreparedRequest("POST", "/sync/mylist", json=body)
        return self._model(await self._transport.request(req), SyncWatchListResponse)

    async def add(
        self, item: Union[WatchlistEntry, list[WatchlistEntry]]
    ) -> SyncWatchListResponse:
        """Alias of :meth:`save` that also accepts a single entry."""
        return await self.save(item if isinstance(item, list) else [item])

    async def get_progress(self, title_id: Any) -> Movie:
        """``GET /titles/{id}/progress`` — the user's entry for a title.

        A title on none of the user's lists comes back with ``list_id == 0``.
        """
        req = PreparedRequest("GET", f"/titles/{title_id}/progress")
        movie = self._model_opt(await self._transport.request(req), Movie)
        return movie or Movie(list_id=0, title=MovieTitle(id=int(title_id)))

    async def update(
        self,
        title_id: Any,
        *,
        status: Optional[StatusLike] = None,
        episode_seen: Optional[int] = None,
        rating: Optional[float] = None,
        date_start: Optional[DateLike] = None,
        date_finish: Optional[DateLike] = None,
        times_rewatched: Optional[int] = None,
        rewatch_value: Optional[int] = None,
        priority: Optional[int] = None,
        note: Optional[str] = None,
        current: Optional[Movie] = None,
    ) -> Movie:
        """Change one title's list entry, keeping every field that is not passed.

        Reads the current entry (or uses ``current``), applies the changes and saves the
        whole entry, since :meth:`save` would reset omitted fields. ``status`` is
        required for a title that is on none of the user's lists. Moving a title to
        :attr:`MovieStatusType.COMPLETED` without an ``episode_seen`` marks every episode
        seen, as the app does. ``rating`` is a score from 0 (unrated) to 10. An empty
        ``note`` leaves the stored note unchanged; the server cannot clear a note.

        Returns the saved entry. Raises :class:`~mdl.errors.MDLSyncError` when the server
        rejects the change (for example "Invalid episode seen value." or "This show has
        not aired yet.") and :class:`ValueError` for arguments it cannot send.
        """
        if rating is not None and not 0 <= rating <= 10:
            raise ValueError("rating must be between 0 and 10")
        if episode_seen is not None and episode_seen < 0:
            raise ValueError("episode_seen cannot be negative")
        new_status = MovieStatusType(status) if status is not None else None
        if new_status is not None and new_status.list_id is None:
            raise ValueError(f"Setting the {new_status.label!r} status is not supported")

        if current is None:
            current = await self.get_progress(title_id)
        changes: dict[str, Any] = {
            "episode_seen": episode_seen,
            "rating": rating,
            "date_start": _date_str(date_start),
            "date_finish": _date_str(date_finish),
            "times_rewatched": times_rewatched,
            "rewatch_value": rewatch_value,
            "priority": priority,
            "note": note,
        }
        if new_status is not None:
            changes["list_id"] = new_status.list_id
        entry = current.model_copy(
            update={key: value for key, value in changes.items() if value is not None}
        )
        if not entry.list_id:
            raise ValueError("status is required for a title that is on none of your lists")
        title = entry.title or MovieTitle(id=int(title_id))
        if (
            new_status is MovieStatusType.COMPLETED
            and episode_seen is None
            and title.episodes
        ):
            entry.episode_seen = title.episodes
        entry.title = title

        await self._save_one(entry)
        if not current.list_id:
            # Re-adding a title that was once removed restores the old entry's
            # progress and note on that first save; save again so the request sticks.
            stored = await self.get_progress(title_id)
            if _progress_differs(stored, entry):
                await self._save_one(entry)
        return entry

    async def _save_one(self, entry: Movie) -> None:
        result = await self.save([entry])
        if result.failures:
            raise MDLSyncError(result.failures)

    async def remove(self, ids: list[int]) -> SyncWatchListResponse:
        """``DELETE /sync/mylist`` — remove titles (by title id) from the user's lists.

        Sends a JSON array body ``[{"id": …}, …]``.
        """
        req = PreparedRequest(
            "DELETE", "/sync/mylist", json=[{"id": i} for i in ids]
        )
        return self._model(await self._transport.request(req), SyncWatchListResponse)


class CustomListsResource(AsyncResource):
    """CustomListRepository (+ detail/items) — user & discovery lists, CRUD, votes."""

    _FEEDS = {
        "friends_voted": "/lists/friends_voted",
        "i_voted": "/lists/i_voted",
        "popular": "/lists/popular_voting_lists",
        "recent_activity": "/lists/recent_activity",
        "trending": "/lists/trending",
        "featured": "/lists/featured",
    }

    async def _feed(self, path: str, page: int, limit: int) -> list[CustomListItem]:
        req = PreparedRequest("GET", path, params={"limit": limit, "page": page})
        return self._list(await self._transport.request(req), CustomListItem)

    async def get_user_lists(
        self, user_id: Any, *, page: int = 2, limit: int = 20
    ) -> list[CustomListItem]:
        return await self._feed(f"/users/{user_id}/lists", page, limit)

    async def friends_voted(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return await self._feed(self._FEEDS["friends_voted"], page, limit)

    async def i_voted(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return await self._feed(self._FEEDS["i_voted"], page, limit)

    async def popular(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return await self._feed(self._FEEDS["popular"], page, limit)

    async def recent_activity(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return await self._feed(self._FEEDS["recent_activity"], page, limit)

    async def trending(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return await self._feed(self._FEEDS["trending"], page, limit)

    async def featured(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return await self._feed(self._FEEDS["featured"], page, limit)

    async def create(
        self,
        *,
        name: str,
        description: str = "",
        list_type: str = "",
        type: str = "",
        sort_by: str = "default",
        vote_limit: int = 100,
        max_num_items: int = 100,
        add_permission: bool = True,
    ) -> CustomListItem:
        body = {
            "name": name,
            "description": description,
            "list_type": list_type,
            "type": type,
            "sort_by": sort_by,
            "vote_start": "",
            "vote_end": "",
            "vote_limit": vote_limit,
            "max_num_items": max_num_items,
            "add_permission": add_permission,
        }
        req = PreparedRequest("POST", "/lists", json=body)
        return self._model(await self._transport.request(req), CustomListItem)

    async def edit(self, list_id: Any, **fields: Any) -> CustomListItem:
        req = PreparedRequest("PATCH", f"/lists/{list_id}", json=fields)
        return self._model(await self._transport.request(req), CustomListItem)

    async def delete(self, list_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/lists/{list_id}")
        return self._bool(await self._transport.request(req))

    async def get_detail(self, list_id: Any) -> CustomListDetail:
        req = PreparedRequest("GET", f"/lists/{list_id}")
        return self._model(await self._transport.request(req), CustomListDetail)

    async def get_votes(self, list_id: Any) -> list[CustomListDetailItem]:
        req = PreparedRequest("GET", f"/lists/{list_id}/votes")
        return self._list(await self._transport.request(req), CustomListDetailItem)

    async def get_watch_status(self, list_id: Any) -> list[WatchStatusList]:
        req = PreparedRequest("GET", f"/lists/{list_id}/watched")
        return self._list(await self._transport.request(req), WatchStatusList)

    async def set_votes(self, list_id: Any, votes: str) -> bool:
        req = PreparedRequest("POST", f"/lists/{list_id}/add", json={"votes": votes})
        return self._bool(await self._transport.request(req))

    async def add_item(self, list_id: Any, entry_id: int) -> bool:
        req = PreparedRequest("POST", f"/lists/{list_id}/add", json={"entry_id": entry_id})
        return self._bool(await self._transport.request(req))

    async def remove_item(self, list_id: Any, item_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/lists/{list_id}/{item_id}")
        return self._bool(await self._transport.request(req))

    async def sort_item(self, list_id: Any, item_id: Any, order: float) -> bool:
        req = PreparedRequest(
            "PATCH", f"/lists/{list_id}/{item_id}/order", json={"order": order}
        )
        return self._bool(await self._transport.request(req))

    async def like(self, list_id: Any, liked: bool = True) -> CustomListLike:
        req = PreparedRequest("POST", f"/lists/{list_id}/likes", json={"liked": liked})
        return self._model(await self._transport.request(req), CustomListLike)

    async def list_comments(
        self, list_id: Any, *, page: int = 1, **params: Any
    ) -> CommentResponse:
        req = PreparedRequest(
            "GET", "/comments", params={"ptype": "clist", "pid": list_id, "page": page, **params}
        )
        return self._model(await self._transport.request(req), CommentResponse)

    async def post_comment(
        self,
        list_id: Any,
        *,
        message: str,
        reply_to: Optional[int] = None,
        spoiler: Optional[int] = None,
    ) -> CommentReplyResponse:
        body: dict[str, Any] = {"pid": list_id, "ptype": "clist", "message": message}
        if reply_to is not None:
            body["reply_to"] = reply_to
        if spoiler is not None:
            body["spoiler"] = spoiler
        req = PreparedRequest("POST", "/comments", json=body)
        return self._model(await self._transport.request(req), CommentReplyResponse)

    async def update_comment(
        self, comment_id: Any, *, message: str, spoiler: Optional[int] = None
    ) -> Optional[Comment]:
        req = PreparedRequest(
            "PATCH", f"/comments/{comment_id}", json={"message": message, "spoiler": spoiler}
        )
        return self._model_opt(await self._transport.request(req), Comment)
