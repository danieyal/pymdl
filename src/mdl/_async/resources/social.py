"""Feeds, articles, friends, messages, notifications and groups resources (spec §3)."""

from __future__ import annotations

from typing import Any, Optional

from ..._request import PreparedRequest
from ...config import UPLOAD_URL
from ...models.auth import ProfileUploadResponse
from ...models.feeds import Article, Embed, Feed, FeedsResponse
from ...models.social import (
    Friend,
    Group,
    ModifiNotificationResponse,
    NotificationResponse,
    ThreadMessageResponse,
)
from .base import AsyncResource


class FeedsResource(AsyncResource):
    """FeedsRepository — the activity feed, posts, embeds and image uploads."""

    async def fetch(self, **params: Any) -> FeedsResponse:
        req = PreparedRequest("GET", "/feeds", params=params or None)
        return self._model(await self._transport.request(req), FeedsResponse)

    async def get(self, feed_id: Any) -> Optional[Feed]:
        params = {"where": "id"} if str(feed_id).isdigit() else None
        req = PreparedRequest("GET", f"/feeds/{feed_id}", params=params)
        return self._model_opt(await self._transport.request(req), Feed)

    async def create(
        self,
        *,
        message: str,
        privacy: str = "public",
        spoiler: bool = False,
        tag_id: Optional[int] = None,
        tag_type: Optional[str] = None,
        attachments: Optional[Any] = None,
        embed_id: Optional[Any] = None,
        group_id: Optional[int] = None,
    ) -> FeedsResponse:
        body: dict[str, Any] = {"privacy": privacy, "message": message, "spoiler": spoiler}
        for key, value in (
            ("tag_id", tag_id),
            ("tag_type", tag_type),
            ("attachments", attachments),
            ("embed_id", embed_id),
            ("group_id", group_id),
        ):
            if value is not None:
                body[key] = value
        req = PreparedRequest("POST", "/feeds", json=body)
        return self._model(await self._transport.request(req), FeedsResponse)

    async def edit(
        self,
        feed_id: Any,
        *,
        message: str,
        spoiler: bool = False,
        tag_id: Optional[int] = None,
        tag_type: Optional[str] = None,
        attachments: Optional[Any] = None,
        embed_id: Optional[Any] = None,
    ) -> FeedsResponse:
        body: dict[str, Any] = {"message": message, "spoiler": spoiler}
        for key, value in (
            ("tag_id", tag_id),
            ("tag_type", tag_type),
            ("attachments", attachments),
            ("embed_id", embed_id),
        ):
            if value is not None:
                body[key] = value
        req = PreparedRequest("PATCH", f"/feeds/{feed_id}", json=body)
        return self._model(await self._transport.request(req), FeedsResponse)

    async def delete(self, feed_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/feeds/{feed_id}")
        return self._bool(await self._transport.request(req))

    async def hide(self, feed_id: Any) -> bool:
        req = PreparedRequest("POST", f"/feeds/{feed_id}/hide")
        return self._bool(await self._transport.request(req))

    async def like(self, feed_id: Any, liked: bool = True) -> bool:
        req = PreparedRequest("POST", f"/feeds/{feed_id}/likes", json={"liked": liked})
        return self._bool(await self._transport.request(req))

    async def upload_image(
        self, content: bytes, *, filename: str = "photo.jpg"
    ) -> Optional[ProfileUploadResponse]:
        req = PreparedRequest(
            "POST",
            UPLOAD_URL,
            multipart=True,
            data={"category": "photos"},
            files={"file": (filename, content)},
        )
        return self._model_opt(await self._transport.request(req), ProfileUploadResponse)

    async def fetch_embed(self, url: str) -> Embed:
        req = PreparedRequest("POST", "/embed", params={"url": url})
        return self._model(await self._transport.request(req), Embed)


class ArticlesResource(AsyncResource):
    """ArticleRepository."""

    async def get(self, article_id: Any) -> Optional[Article]:
        req = PreparedRequest("GET", f"/articles/{article_id}")
        return self._model_opt(await self._transport.request(req), Article)

    async def featured(self, *, page: int = 1) -> list[Article]:
        req = PreparedRequest("GET", "/articles/featured", params={"page": page})
        return self._list(await self._transport.request(req), Article)

    async def like(self, article_id: Any, liked: bool = True) -> bool:
        req = PreparedRequest("POST", f"/articles/{article_id}/likes", json={"liked": liked})
        return self._bool(await self._transport.request(req))


class FriendsResource(AsyncResource):
    """FriendRepository — requests, approve/deny, unfriend."""

    async def requests(self, *, page: int = 1) -> list[Friend]:
        req = PreparedRequest("GET", "/users/requests", params={"page": page})
        return self._list(await self._transport.request(req), Friend)

    async def approve(self, user_id: Any) -> Any:
        req = PreparedRequest("POST", f"/users/{user_id}/approve")
        return self._raw(await self._transport.request(req))

    async def deny(self, user_id: Any) -> Any:
        req = PreparedRequest("DELETE", f"/users/{user_id}/deny")
        return self._raw(await self._transport.request(req))

    async def unfriend(self, user_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/users/{user_id}/unfriend")
        return self._bool(await self._transport.request(req))

    async def send_request(self, user_id: Any) -> bool:
        req = PreparedRequest("POST", f"/users/{user_id}/friend")
        return self._bool(await self._transport.request(req))


class MessagesResource(AsyncResource):
    """MessagesRepository — inbox/outbox threads."""

    async def thread(self, thread_id: Any) -> ThreadMessageResponse:
        req = PreparedRequest("GET", f"/users/inbox/{thread_id}")
        return self._model(await self._transport.request(req), ThreadMessageResponse)

    async def outbox_thread(self, thread_id: Any) -> ThreadMessageResponse:
        req = PreparedRequest("GET", f"/users/outbox/{thread_id}")
        return self._model(await self._transport.request(req), ThreadMessageResponse)

    async def reply(self, thread_id: Any, message: str) -> bool:
        req = PreparedRequest(
            "POST", f"/users/inbox/{thread_id}", json={"from": "inbox", "message": message}
        )
        return self._bool(await self._transport.request(req))

    async def compose(self, *, to: Any, subject: str, message: str) -> bool:
        req = PreparedRequest(
            "POST",
            "/users/inbox/compose",
            json={"to": to, "subject": subject, "message": message},
        )
        return self._bool(await self._transport.request(req))

    async def clear(self, thread_id: Any) -> bool:
        req = PreparedRequest("POST", f"/users/inbox/{thread_id}/clear")
        return self._bool(await self._transport.request(req))


class NotificationsResource(AsyncResource):
    """NotificationsRepository."""

    async def fetch(
        self, *, page: int = 1, limit: Optional[int] = None
    ) -> NotificationResponse:
        params: dict[str, Any] = {"page": page}
        if limit is not None:
            params["limit"] = limit
        req = PreparedRequest("GET", "/notifications", params=params)
        resp = await self._transport.request(req)
        if resp.status_code != 200 or resp.json in (None, ""):
            return NotificationResponse()
        return self._model(resp, NotificationResponse)

    async def clear_all(self) -> Optional[ModifiNotificationResponse]:
        req = PreparedRequest("DELETE", "/notifications")
        return self._model_opt(await self._transport.request(req), ModifiNotificationResponse)

    async def clear(self, notification_id: Any) -> ModifiNotificationResponse:
        req = PreparedRequest("DELETE", f"/notifications/{notification_id}")
        return self._model(await self._transport.request(req), ModifiNotificationResponse)


class GroupsResource(AsyncResource):
    """GroupRepository."""

    async def get(self, group_id: Any) -> Group:
        req = PreparedRequest("GET", f"/groups/{group_id}")
        return self._model(await self._transport.request(req), Group)

    async def join(self, group_id: Any) -> Group:
        req = PreparedRequest("POST", f"/groups/{group_id}/join")
        return self._model(await self._transport.request(req), Group)

    async def leave(self, group_id: Any) -> Group:
        req = PreparedRequest("POST", f"/groups/{group_id}/leave")
        return self._model(await self._transport.request(req), Group)
