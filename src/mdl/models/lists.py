"""Custom-list models (spec §4 'Custom lists')."""

from __future__ import annotations

from typing import Any, Optional

from .base import MDLModel
from .reviews import Author


class CustomListItem(MDLModel):
    """List summary card."""

    list_type: Optional[str] = None
    slug: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    sort_by: Optional[str] = None
    vote_start: Optional[str] = None
    vote_end: Optional[str] = None
    ended: Optional[bool] = None
    started: Optional[bool] = None
    is_owner: Optional[bool] = None
    vote_limit: Optional[int] = None
    max_num_items: Optional[int] = None
    add_permission: Optional[bool] = None
    count: Optional[int] = None
    private: Optional[bool] = None
    preview: Optional[bool] = None
    date_added: Optional[str] = None
    last_updated: Optional[str] = None
    items: Optional[Any] = None
    total_votes: Optional[int] = None
    total_likes: Optional[int] = None
    total_comments: Optional[int] = None
    preview_images: Optional[list[str]] = None  # toJson omits
    liked: Optional[bool] = None  # toJson omits


class CustomListDetailItem(MDLModel):
    id: Optional[int] = None
    eid: Optional[int] = None
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    reason: Optional[str] = None
    sort: Optional[float] = None
    total_points: Optional[int] = None
    total_voters: Optional[int] = None
    vote_order: Optional[int] = None
    curr_rating: Optional[float] = None
    curr_watch_status: Optional[float] = None
    resource_id: Optional[int] = None
    title: Optional[str] = None
    score: Optional[float] = None
    author_score: Optional[float] = None
    content_type: Optional[str] = None
    synopsis: Optional[str] = None
    episodes: Optional[int] = None
    country: Optional[str] = None
    start_date: Optional[str] = None
    category: Optional[str] = None
    stage_name: Optional[str] = None
    nationality: Optional[str] = None
    display_name: Optional[str] = None


class CustomListDetail(MDLModel):
    id: Optional[int] = None
    sid: Optional[int] = None
    author: Optional[Author] = None
    list_type: Optional[str] = None
    lang_iso: Optional[str] = None
    slug: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    sort_by: Optional[str] = None
    total_votes: Optional[int] = None
    total_points: Optional[int] = None
    total_likes: Optional[int] = None
    total_comments: Optional[int] = None
    total_views: Optional[int] = None
    is_owner: Optional[bool] = None
    can_delete: Optional[bool] = None
    deleted: Optional[bool] = None
    vote_limit: Optional[int] = None
    add_permission: Optional[bool] = None
    private: Optional[bool] = None
    preview: Optional[bool] = None
    date_added: Optional[str] = None
    last_updated: Optional[str] = None
    items: Optional[list[CustomListDetailItem]] = None
    liked: Optional[bool] = None
    vote_start: Optional[str] = None
    vote_end: Optional[str] = None
    max_num_items: Optional[int] = None


class WatchStatusList(MDLModel):
    id: Optional[int] = None
    name: Optional[str] = None
    total: Optional[int] = None


class CustomListLike(MDLModel):
    id: Optional[int] = None
    likes: Optional[int] = None
    total: Optional[int] = None
    liked: Optional[bool] = None
    attribute: Optional[Any] = None
