"""Social models: friends, messages, notifications, groups, chat (spec §4)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field

from .base import MDLModel
from .reviews import Author


class Status(MDLModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatarURL: Optional[str] = None
    is_friend: Optional[bool] = None
    request_sent: Optional[bool] = None
    request_pending: Optional[bool] = None
    is_blocking: Optional[bool] = None
    is_blocked: Optional[bool] = None
    is_following: Optional[bool] = None


class Friend(MDLModel):
    """``models/friend/friend.dart`` shape."""

    user_id: Optional[Any] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[Status] = None


class Connections(MDLModel):
    friended: Optional[bool] = None
    friending_requested: Optional[bool] = None
    blocking: Optional[bool] = None


class FriendAlt(MDLModel):
    """``models/friend.dart`` shape."""

    id: Optional[Any] = None
    user_id: Optional[Any] = None
    location: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    connections: Optional[Connections] = None


class ThreadUser(MDLModel):
    username: Optional[str] = None
    vip: Optional[bool] = None
    banned: Optional[bool] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role_name: Optional[str] = None
    role_color: Optional[str] = None


class ThreadMessage(MDLModel):
    id: Optional[int] = None
    pid: Optional[Any] = None
    message: Optional[str] = None
    date_added: Optional[int] = None
    user: Optional[ThreadUser] = None


class _ThreadStats(MDLModel):
    total: Optional[int] = None


class ThreadMessageResponse(MDLModel):
    messages: Optional[list[ThreadMessage]] = None
    stats: Optional[_ThreadStats] = None


class Chat(MDLModel):
    id: Optional[Any] = None
    author: Optional[Author] = None
    subject: Optional[str] = None
    date_added: Optional[int] = None
    last_update: Optional[int] = None
    read_status: Optional[bool] = None
    type: Optional[str] = None
    deleted: Optional[bool] = None


class NotificationFrom(MDLModel):
    avatar_url: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    system: Optional[Any] = None


class NotificationResource(MDLModel):
    id: Optional[Any] = None
    type: Optional[Any] = None
    text: Optional[str] = None
    url: Optional[str] = None


class NotificationObject(MDLModel):
    id: Optional[int] = None
    type: Optional[int] = None
    message: Optional[str] = None
    # ``from`` is a Python keyword; expose it as ``from_`` with an explicit alias.
    from_: Optional[NotificationFrom] = Field(default=None, alias="from")
    resource: Optional[NotificationResource] = None
    viewed: Optional[bool] = None
    created_at: Optional[str] = None


class NotificationResponse(MDLModel):
    notifications: Optional[list[NotificationObject]] = None
    total: Optional[int] = None
    friends: Optional[int] = None
    messages: Optional[int] = None


class ModifiNotificationResponse(MDLModel):
    code: Optional[int] = None
    message: Optional[str] = None


class Group(MDLModel):
    id: int
    name: Optional[str] = None
    is_member: Optional[bool] = None
