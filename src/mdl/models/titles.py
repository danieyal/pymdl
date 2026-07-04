"""Titles, movies & watchlist models (spec §4 'Titles, movies & watchlist')."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import Field, field_validator

from .base import Images, MDLModel, SearchEntry, as_int_flag


class Trailer(MDLModel):
    id: Optional[int] = None


class MovieResourceResponse(MDLModel):
    xid: Optional[str] = None
    name: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    link: Optional[str] = None
    image: Optional[str] = None


class TitleResponse(MDLModel):
    """Full title detail (``GET /titles/{id}?expand=1``)."""

    id: int
    slug: Optional[str] = None
    title: Optional[str] = None
    original_title: Optional[str] = None
    year: Optional[int] = None
    episodes: Optional[int] = None
    rating: Optional[float] = None
    permalink: Optional[str] = None
    synopsis: Optional[str] = None
    type: Optional[str] = None
    language: Optional[str] = None
    images: Optional[Images] = None
    country: Optional[str] = None
    media_type: Optional[str] = None
    votes: Optional[int] = None
    aired_start: Optional[str] = None
    aired_end: Optional[str] = None
    released: Optional[str] = None  # response-only
    trailer: Optional[Trailer] = None
    watchers: Optional[int] = None
    ranked: Optional[int] = None
    popularity: Optional[int] = None
    runtime: Optional[int] = None
    reviews_count: Optional[int] = None
    recs_count: Optional[int] = None
    comments_count: Optional[int] = None
    certification: Optional[str] = None
    status: Optional[str] = None
    updated_at: Optional[int] = None
    release_dates_fmt: Optional[str] = None  # response-only
    enable_ads: Optional[bool] = None  # response-only
    alt_titles: Optional[list[SearchEntry]] = None
    genres: Optional[list[SearchEntry]] = None
    tags: Optional[list[SearchEntry]] = None
    sources: Optional[list[MovieResourceResponse]] = None


class WatchStatusWrapper(MDLModel):
    status: Optional[int] = None


class MovieTitle(MDLModel):
    """Compact title (search / lists / recommendations)."""

    id: int
    title: Optional[str] = None
    synopsis: Optional[str] = None
    original_title: Optional[str] = None
    year: Optional[int] = None
    episodes: Optional[int] = None
    rating: Optional[float] = None
    aired_start: Optional[str] = None
    aired_end: Optional[str] = None
    released: Optional[bool] = None
    type: Optional[str] = None
    media_type: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    images: Optional[Images] = None
    watch_status: Optional[int] = None
    rank: Optional[int] = None
    ended: Optional[bool] = None
    # response key is ``released_date``; request serialization uses ``release_date``.
    released_date: Optional[str] = Field(default=None, serialization_alias="release_date")
    category: Optional[str] = None

    @field_validator("watch_status", mode="before")
    @classmethod
    def _flatten_watch_status(cls, v: Any) -> Optional[int]:
        return as_int_flag(v)


class WatchPoints(MDLModel):
    production: Optional[bool] = None
    story: Optional[bool] = None
    acting: Optional[bool] = None
    visual: Optional[bool] = None
    ost: Optional[bool] = None


class Movie(MDLModel):
    """A watchlist entry: a compact title plus the user's progress."""

    list_id: Optional[int] = None
    episode_seen: Optional[int] = None
    rating: Optional[float] = None
    priority: Optional[int] = None
    times_rewatched: Optional[int] = None
    rewatch_value: Optional[int] = None
    date_start: Optional[str] = None
    date_finish: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[str] = None
    watch_points: Optional[WatchPoints] = None
    updated_at: Optional[str] = None
    title: Optional[MovieTitle] = None
    deleted: Optional[bool] = None  # response-only


class MovieStatusType(str, Enum):
    """Local watch-status enum → watchlist path segment (spec 'MovieStatus')."""

    WATCHING = "watching"
    PLAN_TO_WATCH = "plantowatch"
    COMPLETED = "completed"
    ON_HOLD = "onhold"
    DROPPED = "dropped"
    UNDECIDED = "undecided"
    NOT_INTERESTED = "notinterested"

    @property
    def label(self) -> str:
        return {
            MovieStatusType.WATCHING: "Currently Watching",
            MovieStatusType.PLAN_TO_WATCH: "Plan to watch",
            MovieStatusType.COMPLETED: "Completed",
            MovieStatusType.ON_HOLD: "On hold",
            MovieStatusType.DROPPED: "Dropped",
            MovieStatusType.UNDECIDED: "Undecided",
            MovieStatusType.NOT_INTERESTED: "Not interested",
        }[self]

    def mylist_path(self) -> str:
        return f"/sync/mylist/{self.value}"

    def watchlist_path(self) -> str:
        return f"/watchlist/{self.value}"


class LastActivity(MDLModel):
    """Sync timestamps (``GET /sync/last_activities``)."""

    all: Optional[str] = None
    watching_at: Optional[str] = None
    completed_at: Optional[str] = None
    onhold_at: Optional[str] = None
    plan_to_watch_at: Optional[str] = None
    dropped_at: Optional[str] = None
    not_interested_at: Optional[str] = None
    rated_at: Optional[str] = None
    undecided_at: Optional[str] = None


class _SyncSuccess(MDLModel):
    titles: Optional[int] = None


class _NotFoundEntry(MDLModel):
    id: Optional[int] = None
    title: Optional[str] = None


class _SyncNotFound(MDLModel):
    titles: Optional[list[_NotFoundEntry]] = None


class SyncWatchListResponse(MDLModel):
    success: Optional[_SyncSuccess] = None
    not_found: Optional[_SyncNotFound] = None
    deleted: Optional[Any] = None
