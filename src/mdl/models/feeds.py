"""Feeds, articles & embed models (spec §4 'Feeds, articles, embeds')."""

from __future__ import annotations

from typing import Any, Optional

from .base import MDLModel


class MediaAttachment(MDLModel):
    src: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    ratio: Optional[float] = None
    video: Optional[bool] = None


class FeedComment(MDLModel):
    """Nested comment inside a feed item."""

    id: Optional[int] = None
    message: Optional[str] = None
    likes: Optional[int] = None
    spoiler: Optional[bool] = None
    date_added: Optional[str] = None
    reply_pid: Optional[int] = None
    parent_id: Optional[int] = None
    depth: Optional[int] = None
    can_delete: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_report: Optional[bool] = None
    deleted: Optional[bool] = None
    username: Optional[str] = None
    verified: Optional[bool] = None
    elite: Optional[bool] = None
    role: Optional[Any] = None
    vip: Optional[bool] = None
    awards: Optional[Any] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    liked: Optional[bool] = None


class Feed(MDLModel):
    id: Optional[Any] = None
    author_username: Optional[str] = None
    author_display_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    activity_type: Optional[str] = None
    message: Optional[str] = None
    raw_message: Optional[str] = None
    attachment_images: Optional[list[str]] = None
    media: Optional[list[MediaAttachment]] = None
    tag_id: Optional[int] = None
    tag_type: Optional[str] = None
    content_id: Optional[int] = None
    content_type: Optional[str] = None
    content_title: Optional[str] = None
    content_image: Optional[str] = None
    content_description: Optional[str] = None
    content_category: Optional[str] = None
    content_url: Optional[str] = None
    content_source: Optional[str] = None
    content_sid: Optional[int] = None
    content_status: Optional[str] = None
    content_value: Optional[int] = None
    content_score: Optional[int] = None
    content_percent: Optional[int] = None
    content_episodes: Optional[int] = None
    cached_data: Optional[Any] = None
    comments: Optional[list[FeedComment]] = None
    likes: Optional[list[str]] = None
    spoiler: Optional[bool] = None
    deleted: Optional[bool] = None
    total_likes: Optional[int] = None
    total_comments: Optional[int] = None
    group_name: Optional[str] = None
    liked: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_edit: Optional[bool] = None
    score: Optional[Any] = None
    awards: Optional[Any] = None
    stream: Optional[Any] = None
    date_published: Optional[str] = None
    status: Optional[str] = None


class FeedsResponse(MDLModel):
    batch: Optional[Any] = None
    url: Optional[str] = None
    logged: Optional[bool] = None
    user: Optional[Any] = None
    items: Optional[list[Feed]] = None
    awards: Optional[list[Any]] = None
    current_user: Optional[Any] = None
    relationships: Optional[list[Any]] = None
    tabs: Optional[list[Any]] = None


class ArticleImages(MDLModel):
    image_hash: Optional[str] = None
    thumb: Optional[str] = None
    medium: Optional[str] = None
    poster: Optional[str] = None


class ArticleAuthor(MDLModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    edge_status: Optional[Any] = None
    last_active: Optional[str] = None


class Article(MDLModel):
    id: int
    title: Optional[str] = None
    url: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    image_id: Optional[int] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    images: Optional[ArticleImages] = None
    total_comments: Optional[int] = None
    total_likes: Optional[int] = None
    featured: Optional[bool] = None
    draft: Optional[bool] = None
    published: Optional[bool] = None
    deleted: Optional[bool] = None
    date_added: Optional[str] = None
    publish_date: Optional[str] = None
    author: Optional[ArticleAuthor] = None
    body_text: Optional[str] = None
    liked: Optional[bool] = None
    author_alias: Optional[str] = None


class EmbedImage(MDLModel):
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class EmbedFavicon(MDLModel):
    url: Optional[str] = None


class Embed(MDLModel):
    key: Optional[str] = None
    type: Optional[str] = None
    version: Optional[str] = None
    title: Optional[str] = None
    provider_name: Optional[str] = None
    provider_url: Optional[str] = None
    site: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    msg: Optional[str] = None
    html: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    favicon: Optional[EmbedFavicon] = None
    images: Optional[list[EmbedImage]] = None
    oembed: Optional[Any] = None
