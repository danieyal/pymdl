"""Watchlist sync and custom-list resources (spec §3)."""

from __future__ import annotations

from typing import Any, Optional, Union

from ..._request import PreparedRequest
from ...errors import MDLNotFoundError
from ...models.lists import (
    CustomListDetail,
    CustomListDetailItem,
    CustomListItem,
    CustomListLike,
    WatchStatusList,
)
from ...models.reviews import Comment, CommentReplyResponse, CommentResponse
from ...models.titles import LastActivity, Movie, MovieStatusType, SyncWatchListResponse
from .base import Resource

StatusLike = Union[MovieStatusType, str]


def _status_segment(status: StatusLike) -> str:
    return status.value if isinstance(status, MovieStatusType) else status


class WatchlistResource(Resource):
    """WatchListImplRepository — user's list sync."""

    def fetch(
        self, status: StatusLike, *, last_updated_at: Optional[str] = None
    ) -> list[Movie]:
        """Fetch a status list, e.g. ``/sync/mylist/completed``."""
        params = {"last_updated_at": last_updated_at} if last_updated_at else None
        req = PreparedRequest(
            "GET", f"/sync/mylist/{_status_segment(status)}", params=params
        )
        return self._list(self._transport.request(req), Movie)

    def fetch_page(self, status: StatusLike, *, page: int = 1) -> list[Movie]:
        req = PreparedRequest(
            "GET", f"/sync/mylist/{_status_segment(status)}", params={"page": page}
        )
        return self._list(self._transport.request(req), Movie)

    def get_last_activities(self) -> LastActivity:
        """``GET /sync/last_activities`` — a 404 yields a default (empty) LastActivity."""
        req = PreparedRequest("GET", "/sync/last_activities")
        try:
            resp = self._transport.request(req)
        except MDLNotFoundError:
            return LastActivity()
        return self._model(resp, LastActivity)

    def add(self, item: dict[str, Any]) -> SyncWatchListResponse:
        req = PreparedRequest("POST", "/sync/mylist", json=item)
        return self._model(self._transport.request(req), SyncWatchListResponse)

    def remove(self, ids: list[int]) -> SyncWatchListResponse:
        """``DELETE /sync/mylist`` with a JSON array body ``[{"id": …}, …]``."""
        req = PreparedRequest(
            "DELETE", "/sync/mylist", json=[{"id": i} for i in ids]
        )
        return self._model(self._transport.request(req), SyncWatchListResponse)


class CustomListsResource(Resource):
    """CustomListRepository (+ detail/items) — user & discovery lists, CRUD, votes."""

    _FEEDS = {
        "friends_voted": "/lists/friends_voted",
        "i_voted": "/lists/i_voted",
        "popular": "/lists/popular_voting_lists",
        "recent_activity": "/lists/recent_activity",
        "trending": "/lists/trending",
        "featured": "/lists/featured",
    }

    def _feed(self, path: str, page: int, limit: int) -> list[CustomListItem]:
        req = PreparedRequest("GET", path, params={"limit": limit, "page": page})
        return self._list(self._transport.request(req), CustomListItem)

    def get_user_lists(
        self, user_id: Any, *, page: int = 2, limit: int = 20
    ) -> list[CustomListItem]:
        return self._feed(f"/users/{user_id}/lists", page, limit)

    def friends_voted(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return self._feed(self._FEEDS["friends_voted"], page, limit)

    def i_voted(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return self._feed(self._FEEDS["i_voted"], page, limit)

    def popular(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return self._feed(self._FEEDS["popular"], page, limit)

    def recent_activity(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return self._feed(self._FEEDS["recent_activity"], page, limit)

    def trending(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return self._feed(self._FEEDS["trending"], page, limit)

    def featured(self, *, page: int = 2, limit: int = 20) -> list[CustomListItem]:
        return self._feed(self._FEEDS["featured"], page, limit)

    def create(
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
        return self._model(self._transport.request(req), CustomListItem)

    def edit(self, list_id: Any, **fields: Any) -> CustomListItem:
        req = PreparedRequest("PATCH", f"/lists/{list_id}", json=fields)
        return self._model(self._transport.request(req), CustomListItem)

    def delete(self, list_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/lists/{list_id}")
        return self._bool(self._transport.request(req))

    def get_detail(self, list_id: Any) -> CustomListDetail:
        req = PreparedRequest("GET", f"/lists/{list_id}")
        return self._model(self._transport.request(req), CustomListDetail)

    def get_votes(self, list_id: Any) -> list[CustomListDetailItem]:
        req = PreparedRequest("GET", f"/lists/{list_id}/votes")
        return self._list(self._transport.request(req), CustomListDetailItem)

    def get_watch_status(self, list_id: Any) -> list[WatchStatusList]:
        req = PreparedRequest("GET", f"/lists/{list_id}/watched")
        return self._list(self._transport.request(req), WatchStatusList)

    def set_votes(self, list_id: Any, votes: str) -> bool:
        req = PreparedRequest("POST", f"/lists/{list_id}/add", json={"votes": votes})
        return self._bool(self._transport.request(req))

    def add_item(self, list_id: Any, entry_id: int) -> bool:
        req = PreparedRequest("POST", f"/lists/{list_id}/add", json={"entry_id": entry_id})
        return self._bool(self._transport.request(req))

    def remove_item(self, list_id: Any, item_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/lists/{list_id}/{item_id}")
        return self._bool(self._transport.request(req))

    def sort_item(self, list_id: Any, item_id: Any, order: float) -> bool:
        req = PreparedRequest(
            "PATCH", f"/lists/{list_id}/{item_id}/order", json={"order": order}
        )
        return self._bool(self._transport.request(req))

    def like(self, list_id: Any, liked: bool = True) -> CustomListLike:
        req = PreparedRequest("POST", f"/lists/{list_id}/likes", json={"liked": liked})
        return self._model(self._transport.request(req), CustomListLike)

    def list_comments(
        self, list_id: Any, *, page: int = 1, **params: Any
    ) -> CommentResponse:
        req = PreparedRequest(
            "GET", "/comments", params={"ptype": "clist", "pid": list_id, "page": page, **params}
        )
        return self._model(self._transport.request(req), CommentResponse)

    def post_comment(
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
        return self._model(self._transport.request(req), CommentReplyResponse)

    def update_comment(
        self, comment_id: Any, *, message: str, spoiler: Optional[int] = None
    ) -> Optional[Comment]:
        req = PreparedRequest(
            "PATCH", f"/comments/{comment_id}", json={"message": message, "spoiler": spoiler}
        )
        return self._model_opt(self._transport.request(req), Comment)
