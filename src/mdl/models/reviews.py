"""Reviews, comments & credits models (spec §4 'Reviews, comments, credits')."""

from __future__ import annotations

from typing import Any, Optional

from .base import Images, MDLModel
from .titles import MovieTitle


class Ratings(MDLModel):
    story: Optional[float] = None
    acting: Optional[float] = None
    music: Optional[float] = None
    rewatch: Optional[float] = None
    overall: Optional[float] = None


class ReviewAuthor(MDLModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ReviewTitleRef(MDLModel):
    id: Optional[int] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    year: Optional[int] = None
    images: Optional[Images] = None


class ReviewResponse(MDLModel):
    id: int
    ratings: Optional[Ratings] = None
    headline: Optional[str] = None
    review: Optional[str] = None
    version: Optional[int] = None
    upvotes: Optional[int] = None
    total_votes: Optional[int] = None
    completed: Optional[bool] = None
    dropped: Optional[bool] = None
    spoiler: Optional[bool] = None
    lang_iso: Optional[str] = None
    comments: Optional[int] = None
    voted: Optional[int] = None
    episodes: Optional[int] = None
    episodes_seen: Optional[int] = None
    author: Optional[ReviewAuthor] = None
    title: Optional[ReviewTitleRef] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    language: Optional[str] = None


class Author(MDLModel):
    """Comment author (also used across lists/feeds)."""

    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    vip: Optional[bool] = None
    star: Optional[bool] = None
    verified: Optional[bool] = None


class Comment(MDLModel):
    id: int
    comment: Optional[str] = None
    message: Optional[str] = None
    likes: Optional[int] = None
    spoiler: Optional[bool] = None
    parent_id: Optional[int] = None
    depth: Optional[int] = None
    deleted: Optional[bool] = None
    edited: Optional[bool] = None
    liked: Optional[bool] = None
    author: Optional[Author] = None
    role: Optional[Any] = None
    date_added: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CommentResponse(MDLModel):
    comments: Optional[list[Comment]] = None
    authors: Optional[Any] = None
    total: Optional[int] = None


class PostComment(MDLModel):
    id: int
    message: Optional[str] = None
    likes: Optional[int] = None
    replies: Optional[int] = None
    spoiler: Optional[bool] = None
    date_added: Optional[str] = None
    reply_pid: Optional[int] = None
    parent_id: Optional[int] = None
    depth: Optional[int] = None
    can_delete: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_report: Optional[bool] = None
    deleted: Optional[bool] = None
    author: Optional[Author] = None
    role: Optional[Any] = None
    awards: Optional[Any] = None
    liked: Optional[bool] = None


class CommentReplyResponse(MDLModel):
    """Reply thread returned by ``POST /comments``."""

    authors: Optional[Any] = None
    comments: Optional[list[PostComment]] = None
    summary: Optional[Any] = None
    total: Optional[int] = None
    logged: Optional[bool] = None
    has_more: Optional[bool] = None
    disabled: Optional[bool] = None
    lang: Optional[str] = None
    awards: Optional[Any] = None
    roles: Optional[Any] = None
    current_user: Optional[Any] = None
    notes: Optional[Any] = None


class Cast(MDLModel):
    id: Optional[int] = None
    name: Optional[str] = None
    images: Optional[Images] = None
    character_name: Optional[str] = None
    role: Optional[str] = None
    title: Optional[MovieTitle] = None
    also_known_as: Optional[Any] = None


class Crew(MDLModel):
    id: Optional[int] = None
    name: Optional[str] = None
    images: Optional[Images] = None
    job: Optional[str] = None
    role: Optional[str] = None
    title: Optional[MovieTitle] = None


class CreditsResponse(MDLModel):
    cast: Optional[list[Cast]] = None
    crew: Optional[list[Crew]] = None


class ReportRuleResponse(MDLModel):
    rules: Optional[list[Any]] = None
    site_rules: Optional[list[str]] = None
